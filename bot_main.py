import asyncio
import sys

import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message


from token_data import TOKEN
from recipes_handler import router

dp = Dispatcher()
dp.include_router(router)

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    await message.answer(f'Привет! Давай подберём тебе рецепты с:')
    await message.answer(
        f"Напиши мне команду \n /category_search_random и сколько рецептов хочешь посмотреть. \n\n" \
        f"Например: \n /category_search_random 3"
        )

async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == "__main__":
   logging.basicConfig(level=logging.INFO, stream=sys.stdout)
   asyncio.run(main())
