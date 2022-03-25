from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import psycopg2
import os
import logging
from aiogram.utils.executor import start_webhook

from config import TOKEN, DB_URI


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

conn = psycopg2.connect(DB_URI, sslmode = "require")
cur = conn.cursor()

chatdb = "NameOfDataBase"

@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nНапиши-ка мне любой текст и я его повторю!")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Напиши мне что-нибудь, и я отпрпавлю этот текст тебе в ответ!")

HEROKU_APP_NAME = os.getenv('itrevolutionbot')

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = os.getenv('PORT', default=8000)


async def on_startup(dispatcher):
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)


async def on_shutdown(dispatcher):
    await bot.delete_webhook()


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(message.text)


# @dp.message_handler(commands=['add_db'])
# async def process_add_db_command(message: types.Message):
#     global chatdb
#     chatdb = message.chat.id
#     chatdb = str(chatdb)
#     chatdb = chatdb.replace("-", "")
#     chatdb = "group" + chatdb
#     cur.execute(f"CREATE TABLE IF NOT EXISTS {chatdb} (id INTEGER UNIQUE, username VARCHAR(60) UNIQUE, fio VARCHAR(60), birthday VARCHAR(60),vacation_start VARCHAR(60), vacation_end VARCHAR(60))")
#     await message.reply(f"Таблица {chatdb} успешно создана! Прошу админа перейти в ЛС!")
#
# @dp.message_handler(commands=['delete_db'])
# async def process_add_db_command(message: types.Message):
#     global chatdb
#     chatdb = message.chat.id
#     chatdb = str(chatdb)
#     chatdb = chatdb.replace("-", "")
#     chatdb = "group" + chatdb
#     cur.execute(f"DROP TABLE {chatdb}")
#     await message.reply(f"Таблица {chatdb} успешно удалена!")
#
#
# @dp.message_handler(commands=['add_to_db'])
# async def process_add_db_command(message: types.Message):
#     await message.reply(f"Вы добавляете данные в таблицу {chatdb}")
#     await message.reply("Введите данные о пользователе:\nПример:\nUsername: @nekochort\nID: 466280885\nФИО: Шорников Никита Сергеевич\nДень рождения: 27.10\nДата начала отпуска: 26.12.2021\nДата окончания отпуска: 28.01.2022")
#     @dp.message_handler(content_types=["text"])
#     async def process_add_db(message: types.Message):
#         global chatdb
#         send = message.text
#         ls = send.split("\n", 5)
#         username = ls[0]
#         username = "'" + username + "'"
#         userid = ls[1]
#         fio = ls[2]
#         fio = "'" + fio + "'"
#         birthday = ls[3]
#         birthday = "'" + birthday + "'"
#         vacation_start = ls[4]
#         vacation_start = "'" + vacation_start + "'"
#         vacation_end = ls[5]
#         vacation_end = "'" + vacation_end + "'"
#         await message.reply("Имя пользователя: " + ls[0])
#         await message.reply("ID пользователя: " + ls[1])
#         await message.reply("ФИО пользователя: " + ls[2])
#         await message.reply("День рождения: " + ls[3])
#         await message.reply("Дата начала отпуска: " + ls[4])
#         await message.reply("Дата окончания отпуска: " + ls[5])
#         await message.reply(f"Данные занесены в таблицу {chatdb}")
#         cur.execute(f"INSERT INTO {chatdb} (id,username, fio, birthday, vacation_start, vacation_end) VALUES ({userid},{username}, {fio}, {birthday}, {vacation_start}, {vacation_end})")
#
# @dp.message_handler(commands=['delete_from_db'])
# async def process_add_db_command(message: types.Message):
#     await message.reply(f"Вы удаляете данные из таблицы {chatdb}")
#     await message.reply("Введите username пользователя, которого хотите удалить из таблицы")
#     @dp.message_handler(content_types=["text"])
#     async def process_add_db(message: types.Message):
#         global chatdb
#         send = message.text
#         ls = send.split("\n", 5)
#         username = ls[0]
#         username = "'" + username + "'"
#         cur.execute(f"DELETE FROM {chatdb} WHERE username = {username}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )