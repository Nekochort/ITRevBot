import asyncio
from asyncio import WindowsSelectorEventLoopPolicy

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
import psycopg
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

from config import TOKEN, DB_URI

class FSMAddTbl(StatesGroup):
    addtogrptable = State()
class FSMDel(StatesGroup):
    deletefrmtable = State()



bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

chatdb = "NameOfDataBase"



@dp.message_handler(commands=['start'])
async def process_start_command(message: types.Message):
    await message.reply("Привет!\nНапиши-ка мне любой текст и я его повторю!")


@dp.message_handler(commands=['help'])
async def process_help_command(message: types.Message):
    await message.reply("Напиши мне что-нибудь, и я отпрпавлю этот текст тебе в ответ!")

async def adddb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"CREATE TABLE IF NOT EXISTS {chatdb} (id Bigint UNIQUE, username VARCHAR(60) UNIQUE, fio VARCHAR(60), birthday VARCHAR(60),vacation_start VARCHAR(60), vacation_end VARCHAR(60))")


@dp.message_handler(commands='add_db') # Создние таблицы чата
async def process_add_db_command(message: types.Message):
    global chatdb
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    await adddb(chatdb)
    await message.reply(f"Таблица {chatdb} успешно создана! Прошу админа перейти в ЛС!")

async def deletedb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {chatdb}")

@dp.message_handler(commands=['delete_db']) # Удаление таблицы чата
async def process_add_db_command(message: types.Message):
    global chatdb
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    await deletedb(chatdb)
    await message.reply(f"Таблица {chatdb} успешно удалена!")

async def addtodb(chatdb,userid,username,fio,birthday,vacation_start,vacation_end):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {chatdb} (id,username, fio, birthday, vacation_start, vacation_end) VALUES ({userid},{username}, {fio}, {birthday}, {vacation_start}, {vacation_end})")


@dp.message_handler(commands='add_to_db', state=None) #добавление в таблицу
async def process_add_db_command(message: types.Message):
    await message.reply(f"Вы добавляете данные в таблицу {chatdb}")
    await FSMAddTbl.addtogrptable.set()
    await message.reply("Введите данные о пользователе:\nПример:\nUsername: @nekochort\nID: 466280885\nФИО: Шорников Никита Сергеевич\nДень рождения: 27.10\nДата начала отпуска: 26.12.2021\nДата окончания отпуска: 28.01.2022")
    @dp.message_handler(content_types=["text"], state=FSMAddTbl.addtogrptable)
    async def process_add_db(message: types.Message, state: FSMContext):
        global chatdb
        send = message.text
        ls = send.split("\n", 5)
        username = ls[0]
        username = "'" + username + "'"
        userid = ls[1]
        fio = ls[2]
        fio = "'" + fio + "'"
        birthday = ls[3]
        birthday = "'" + birthday + "'"
        vacation_start = ls[4]
        vacation_start = "'" + vacation_start + "'"
        vacation_end = ls[5]
        vacation_end = "'" + vacation_end + "'"
        await message.reply(f"Данные о пользователе {username} занесены в таблицу {chatdb}")
        await addtodb(chatdb,userid,username,fio, birthday, vacation_start, vacation_end)


async def delformdb(chatdb,username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DELETE FROM {chatdb} WHERE username = {username}")

@dp.message_handler(commands='delete_from_db', state=None)
async def process_add_db_command(message: types.Message):
    await message.reply(f"Вы удаляете данные из таблицы {chatdb}")
    await FSMDel.deletefrmtable.set()
    await message.reply("Введите username пользователя, которого хотите удалить из таблицы")
    @dp.message_handler(content_types="text", state=FSMDel.deletefrmtable)
    async def process_add_db(message: types.Message, state: FSMContext):
        global chatdb
        send = message.text
        ls = send.split("\n", 5)
        username = ls[0]
        username = "'" + username + "'"
        await delformdb(chatdb,username)
        await message.reply(f"Пользователь {username} удалён из таблицы!")

if __name__ == '__main__':
    executor.start_polling(dp)