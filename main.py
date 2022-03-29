import asyncio
from asyncio import WindowsSelectorEventLoopPolicy

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
import psycopg
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton
import telebot

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

# Создание таблицы с подписками на уведы
class addnotifdb(StatesGroup):
    addnotdb = State()

@dp.message_handler(commands=["add_notifdb"], state="*")
async def start_command(message: types.Message, state: FSMContext):
    global notifinchatid
    notifinchatid = "Notif" + chatdb
    timemanagment = birthdaynotif = weekmeeting = vacationnotif = True
    await addnotifdb.addnotdb.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"CREATE TABLE IF NOT EXISTS {notifinchatid} (id Bigint UNIQUE, username VARCHAR(60) UNIQUE, timemanagment BOOLEAN, birthdaynotif BOOLEAN, weekmeeting BOOLEAN, vacationnotif BOOLEAN )")
            await acur.execute(f"INSERT INTO {notifinchatid}(id, username) SELECT id, username FROM {chatdb}")
            await acur.execute(f"UPDATE {notifinchatid} SET timemanagment = true,birthdaynotif = true, weekmeeting = true, vacationnotif = true  ")
            await message.answer(f"Таблица уведомлений для {chatdb} успешно создана!")
    await state.finish()


async def adddb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"CREATE TABLE IF NOT EXISTS {chatdb} (id Bigint UNIQUE, username VARCHAR(60) UNIQUE, fio VARCHAR(60), birthday VARCHAR(60),vacation_start VARCHAR(60), vacation_end VARCHAR(60))")

class addchatdb(StatesGroup):
    adddb = State()

@dp.message_handler(commands='add_db', state="*") # Создние таблицы чата
async def process_add_db_command(message: types.Message, state: FSMContext):
    global chatdb
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    await addchatdb.adddb.set()
    await adddb(chatdb)
    await message.reply(f"Таблица {chatdb} успешно создана! Прошу админа перейти в ЛС!")
    await state.finish()

async def deletedb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {chatdb}")

class deletetable(StatesGroup):
    deltable = State()

@dp.message_handler(commands=['delete_db'], state="*") # Удаление таблицы чата
async def process_add_db_command(message: types.Message, state: FSMContext):
    global chatdb
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    await deletetable.deltable.set()
    await deletedb(chatdb)
    await message.reply(f"Таблица {chatdb} успешно удалена!")
    await state.finish()

async def deletnotifdb(chatdb):
    notifinchatid = "Notif" + chatdb
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {notifinchatid}")

class deletentable(StatesGroup):
    delntable = State()

@dp.message_handler(commands=['delete_notif_db'], state="*") # Удаление таблицы чата
async def process_add_db_command(message: types.Message, state: FSMContext):
    global chatdb
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    notifinchatid = "Notif" + chatdb
    await deletentable.delntable.set()
    await deletnotifdb(chatdb)
    await message.reply(f"Таблица {notifinchatid} успешно удалена!")
    await state.finish()

class add(StatesGroup):
    useradd = State()


async def addtodb(chatdb,userid,username,fio,birthday,vacation_start,vacation_end):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {chatdb} (id,username, fio, birthday, vacation_start, vacation_end) VALUES ({userid},{username}, {fio}, {birthday}, {vacation_start}, {vacation_end})")



@dp.message_handler(commands="add_to_db", state="*")
async def add_step(message: types.Message, state: FSMContext):
    await message.reply(text=f'Вы добавляете пользователя в таблицу {chatdb}')
    await message.answer("Введите данные о пользователе:\nПример:\nUsername: @nekochort\nID: 466280885\nФИО: Шорников Никита Сергеевич\nДень рождения: 27.10\nДата начала отпуска: 26.12.2021\nДата окончания отпуска: 28.01.2022")
    await add.useradd.set()


@dp.message_handler(state=add.useradd, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
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
    try:
        await addtodb(chatdb,userid,username,fio, birthday, vacation_start, vacation_end)
        await message.reply(f"Данные о пользователе {username} занесены в таблицу {chatdb}")
    except:
        await message.answer("Проверьте данные!")
    await state.finish()

class delete(StatesGroup):
    deluser = State()


async def delformdb(chatdb, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DELETE FROM {chatdb} WHERE username = {username}")


@dp.message_handler(commands="delete_from_db", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.reply(text=f'Вы удаляете данные из таблицы {chatdb}')
    await message.answer("Введите username пользователя, которого хотите удалить из таблицы")
    await delete.deluser.set()


@dp.message_handler(state=delete.deluser, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    send = message.text
    ls = send.split("\n", 5)
    username = ls[0]
    username = "'" + username + "'"
    await delformdb(chatdb, username)
    await message.reply(f"Пользователь {username} удалён из таблицы!")
    await state.finish()

class edchdb(StatesGroup):
    editdb = State()

# Команда вызова команд для редактирвания основной БД чата
@dp.message_handler(commands=['edit_chat_db'], state="*")
async def edit_command(message: types.Message, state: FSMContext):
    await edchdb.editdb.set()
    await message.answer("Выберите нужные команды и отправьте в личные сообщения боту:\n1)/edit_username - редактирование username пользователя\n2)/edit_fio - редактирование ФИО\n3)/edit_birthday - редактирование дней рождений\n4)/edit_vacation - редактирование дат отпусков")
    await state.finish()

class redun(StatesGroup):
    unred = State()

# Редактирование username
async def username_red(chatdb, newusername, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"UPDATE {chatdb} SET username = {newusername} WHERE username = {username}")


@dp.message_handler(commands=['edit_username'], state="*")
async def unred_command(message: types.Message, state: FSMContext):
    await message.answer(f'Вы собираетесь изменить username пользвателя из таблицы {chatdb}')
    await message.answer("Введите username пользователя, а также устанавливаемый username")
    await redun.unred.set()

@dp.message_handler(state=redun.unred, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    send = message.text
    ls = send.split("\n", 1)
    username = ls[0]
    username = "'" + username + "'"
    newusername = ls[1]
    await message.answer("Username: " + ls[0])
    await message.answer("Устанавливаемый username: " + ls[1])
    newusername = "'" + newusername + "'"
    try:
        await username_red(chatdb, newusername, username)
        await message.reply(f"Username пользователя {username} изменён в таблице {chatdb}")
    except:
        await message.answer("Проверьте данные!")
    await state.finish()

# Редактирование ФИО
async def fio_red(chatdb, newfio, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"UPDATE {chatdb} SET fio = {newfio} WHERE username = {username}")

class redfio(StatesGroup):
    fiored = State()

@dp.message_handler(commands=['edit_fio'], state="*")
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(f'Вы собираетесь изменить ФИО пользвателя из таблицы {chatdb}')
    await message.answer("Введите username пользователя, а также ФИО, которое нужно установить")
    await redfio.fiored.set()

@dp.message_handler(state=redfio.fiored, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    send = message.text
    ls = send.split("\n", 1)
    username = ls[0]
    username = "'" + username + "'"
    newfio = ls[1]
    await message.answer("Username: " + ls[0])
    await message.answer("Устанавливаемое ФИО: " + ls[1])
    newfio = "'" + newfio + "'"
    try:
        await fio_red(chatdb, newfio, username)
        await message.reply(f"ФИО пользователя {username} изменены в таблице {chatdb}")
    except:
        await message.answer("Проверьте данные!")
    await state.finish()

# Редактирование ДР
async def dr_red(chatdb, newbirthday, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"UPDATE {chatdb} SET birthday = {newbirthday} WHERE username = {username}")

class redbd(StatesGroup):
    bdred = State()

@dp.message_handler(commands=['edit_birthday'], state="*")
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(f'Вы собираетесь изменить день рождения пользвателя из таблицы {chatdb}')
    await message.answer("Введите username пользователя, а также устанавливаемую дату дня рождения")
    await redbd.bdred.set()

@dp.message_handler(state=redbd.bdred, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    send = message.text
    ls = send.split("\n", 1)
    username = ls[0]
    username = "'" + username + "'"
    newbirthday = ls[1]
    await message.answer("Username: " + ls[0])
    await message.answer("Устанавливаемый день рождения: " + ls[1])
    newbirthday = "'" + newbirthday + "'"
    try:
        await dr_red(chatdb, newbirthday, username)
        await message.reply(f"День рождения {username} изменён в таблице {chatdb}")
    except:
        await message.answer("Проверьте данные!")
    await state.finish()

# Редактирвание отпусков
async def vac_red(chatdb, newvacationstart, newvacationend, username):
    try:
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"UPDATE {chatdb} SET vacation_start = {newvacationstart} WHERE username = {username}")
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"UPDATE {chatdb} SET vacation_end = {newvacationend} WHERE username = {username}")
    except:
        pass

class redvac(StatesGroup):
    vacred = State()

@dp.message_handler(commands=['edit_vacation'], state="*")
async def start_command(message: types.Message, state: FSMContext):
    await message.answer(f'Вы собираетесь изменить отпуска пользвателя из таблицы {chatdb}')
    await message.answer("Введите username пользователя, а также устанавливаемые даты начала и конца отпуска")
    await redvac.vacred.set()
    await vac_red(message)

@dp.message_handler(state=redvac.vacred, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    send = message.text
    ls = send.split("\n", 2)
    username = ls[0]
    newvacationstart = ls[1]
    newvacationend = ls[2]
    await message.answer("Username: " + ls[0])
    await message.answer("Устанавливаемая дата начала отпуска: " + ls[1])
    await message.answer("Устанавливаемая дата конца отпуска: " + ls[2])
    username = "'" + username + "'"
    newvacationstart = "'" + newvacationstart + "'"
    newvacationend = "'" + newvacationend + "'"
    try:
        await vac_red(chatdb, newvacationstart, newvacationend, username)
        await message.reply(f"Даты отпусков {username} изменены в таблице {chatdb}")
    except:
        await message.answer("Проверьте данные!")
    await state.finish()

# @dp.message_handler(commands=["edit_notif_settings"])
# def menu(message):
#     start_menu = types.ReplyKeyboardMarkup(
#         row_width=3, resize_keyboard=True, one_time_keyboard=True
#     )
#     start_menu.add(
#         "День рождения",
#         "Отпуска",
#         "Списание рабочего времени",
#         "Еженедельное совещание",
#     )
#     bot.send_message(
#         message.chat.id,
#         "Выберите уведомление на которое хотите изменить подписку",
#         reply_markup=start_menu,
#     )
#
#     @bot.message_handler(content_types=["text"])
#     def handle_text(message):
#         if message.text == "День рождения":
#             source_menu = types.ReplyKeyboardMarkup(
#                 row_width=3, resize_keyboard=True, one_time_keyboard=True
#             )
#             source_menu.add("Подписаться", "Отписаться")
#             source_menu.add("Назад")
#             s = bot.send_message(
#                 message.chat.id, "Выберите вариант: ", reply_markup=source_menu
#             )
#             bot.register_next_step_handler(s, handle_text1)
#         elif message.text == "Отпуска":
#             source_menu = types.ReplyKeyboardMarkup(
#                 row_width=3, resize_keyboard=True, one_time_keyboard=True
#             )
#             source_menu.add(
#                 "Подписаться на уведомления об отпусках",
#                 "Отписаться от уведомлений об отпусках",
#             )
#             source_menu.add("Назад")
#             s = bot.send_message(
#                 message.chat.id, "Выберите вариант: ", reply_markup=source_menu
#             )
#             bot.register_next_step_handler(s, handle_text2)
#         elif message.text == "Списание рабочего времени":
#             source_menu = types.ReplyKeyboardMarkup(
#                 row_width=3, resize_keyboard=True, one_time_keyboard=True
#             )
#             source_menu.add(
#                 "Подписаться на уведомления о списании рабочего времени",
#                 "Отписаться от уведомлений о списании рабочего времени"
#             )
#             source_menu.add("Назад")
#             s = bot.send_message(
#                 message.chat.id, "Выберите вариант: ", reply_markup=source_menu
#             )
#             bot.register_next_step_handler(s, handle_text3)
#         elif message.text == "Еженедельное совещание":
#             source_menu = types.ReplyKeyboardMarkup(
#                 row_width=3, resize_keyboard=True, one_time_keyboard=True
#             )
#             source_menu.add(
#                 "Подписаться на уведомления о EC", "Отписаться от уведомлений о EC"
#             )
#             source_menu.add("Назад")
#             s = bot.send_message(
#                 message.chat.id, "Выберите вариант: ", reply_markup=source_menu
#             )
#             bot.register_next_step_handler(s, handle_text4)
#
#
# def handle_text1(message):
#     if message.text == "Отписаться":
#         bot.send_message(
#             message.chat.id, "Вы отписались от уведомлений о Днях рождения"
#         )
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET birthdaynotif = false WHERE id = {message.from_user.id}")
#
#     elif message.text == "Подписаться":
#         bot.send_message(
#             message.chat.id, "Вы подписались на уведомления о Днях рождения"
#         )
#
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET birthdaynotif = true WHERE id = {message.from_user.id}")
#     elif message.text == "Назад":
#         menu(message)
#
#
# def handle_text2(message):
#     if message.text == "Отписаться от уведомлений об отпусках":
#         bot.send_message(message.chat.id, "Вы отписались от уведомлений об отпусках")
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET vacationnotif = false WHERE id = {message.from_user.id}")
#     elif message.text == "Подписаться на уведомления об отпусках":
#         bot.send_message(message.chat.id, "Вы подписались на уведомления об отпусках")
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET vacationnotif = true WHERE id = {message.from_user.id}")
#     elif message.text == "Назад":
#         menu(message)
#
#
# def handle_text3(message):
#     if message.text == "Отписаться от уведомлений о списании рабочего времени":
#         bot.send_message(message.chat.id, "Вы отписались от уведомлений о списании рабочего времени")
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET timemanagment = false WHERE id = {message.from_user.id}")
#     elif message.text == "Подписаться на уведомления о списании рабочего времени":
#         bot.send_message(message.chat.id, "Вы подписались на уведомления о списании рабочего времени")
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET timemanagment = true WHERE id = {message.from_user.id}")
#     elif message.text == "Назад":
#         menu(message)
#
#
# def handle_text4(message):
#     if message.text == "Отписаться от уведомлений о EC":
#         bot.send_message(message.chat.id, "Вы отписались от уведомлений о ЕС")
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET weekmeeting = false WHERE id = {message.from_user.id}")
#     elif message.text == "Подписаться на уведомления о EC":
#         bot.send_message(message.chat.id, "Вы подписались на уведомления о ЕС")
#         async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
#             async with aconn.cursor() as acur:
#                 await acur.execute(f"UPDATE {notifinchatid} SET weekmeeting = true WHERE id = {message.from_user.id}")
#     elif message.text == "Назад":
#         menu(message)


if __name__ == '__main__':
    executor.start_polling(dp)