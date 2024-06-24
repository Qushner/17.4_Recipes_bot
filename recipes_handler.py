import aiohttp
from random import sample
from googletrans import Translator

from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.formatting import (
    as_list, as_marked_section
)
from aiogram import F

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types


class Recipes(StatesGroup):
    number_of_recipes = State()
    random_recipes = State()


router = Router()


@router.message(Command("category_search_random"))  # eg: /category_search_random 5
async def category_search_random(message: Message, command: CommandObject, state: FSMContext):
    if command.args is None:
        await message.answer("Ошибка: не переданы аргументы")
        return

    await state.set_data({'number_of_recipes': command.args})

    async with aiohttp.ClientSession() as session:
        async with session.get('http://www.themealdb.com/api/json/v1/1/list.php?c=list', ) as resp:
            data = await resp.json()
            categories = [item['strCategory'] for item in data['meals']]

    builder = ReplyKeyboardBuilder()
    for item in categories:
        builder.add(types.KeyboardButton(text=item))
    builder.adjust(5)

    await message.answer(
        f"Выберите категорию:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

    await state.set_state(Recipes.number_of_recipes.state)


@router.message(Recipes.number_of_recipes)
async def recipes_by_category(message: types.Message, state: FSMContext):
    number_of_recipes = await state.get_data()
    async with aiohttp.ClientSession() as session:
        async with session.get(f'http://www.themealdb.com/api/json/v1/1/filter.php?c={message.text}', ) as resp:
            data = await resp.json()
            meals = [item for item in data['meals']]
            random_meals = sample(meals, k=int(number_of_recipes["number_of_recipes"]))

            await state.set_data({'random_recipes': [i['idMeal'] for i in random_meals]})

    translator = Translator()
    random_meals_in_russian = []
    for recipe in random_meals:
        random_meals_in_russian.append(
            translator.translate(recipe['strMeal'], dest='ru').text
        )

    kb = [
        [types.KeyboardButton(text='Покажи рецепты')],
    ]

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )

    response = as_list(
        as_marked_section("Как Вам такие варианты: ", *random_meals_in_russian, marker="♨"),
    )
    await message.answer(**response.as_kwargs(), reply_markup=keyboard)

    await state.set_state(Recipes.random_recipes.state)


@router.message(Recipes.random_recipes, F.text.lower() == 'покажи рецепты')
async def recipes_by_id(message: types.Message, state: FSMContext):
    random_recipes_id = await state.get_data()
    async with aiohttp.ClientSession() as session:
        for id in random_recipes_id['random_recipes']:
            async with session.get(f'http://www.themealdb.com/api/json/v1/1/lookup.php?i={id}', ) as resp:
                data = await resp.json()

                for item in data.get('meals'):
                    ingredients = [v for k, v in item.items() if k.startswith('strIngredient') and v]

                translator = Translator()
                recipe_en = [data['meals'][0]['strMeal'],          #Название
                             data['meals'][0]['strInstructions'],  #Рецепт
                             ', '.join(ingredients)]               #Ингридиенты
                recipe_ru = translator.translate(recipe_en, src='en', dest='ru')
                recipe = f"{recipe_ru[0].text} \n\n" \
                         f"Рецепт:\n " \
                         f"{recipe_ru[1].text} \n\n" \
                         f"Ингредиенты: {recipe_ru[2].text}"
                await message.answer(recipe)
