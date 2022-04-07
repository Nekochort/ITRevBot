import asyncio
import logging
from asyncio import WindowsSelectorEventLoopPolicy

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import state
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
import psycopg
import arrow
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN, DB_URI

from aiogram.dispatcher.filters import BoundFilter

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)

class FSMAddTbl(StatesGroup):
    addtogrptable = State()


class FSMDel(StatesGroup):
    deletefrmtable = State()


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

chatdb = "NameOfDataBase"

adminlist = "adminlist"

listofadmins = []

notiflist = []

taglist = []

chatlist = []

scheduler = AsyncIOScheduler()

async def removeshed(id):
    scheduler.remove_job(id)

class MyFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.is_chat_admin()

dp.filters_factory.bind(MyFilter)

@dp.message_handler(commands=["start"])
async def start_com(message: types.Message):
    await message.reply("Привет! Я бот IT-Rev!\nДля подробного описания команд, введите команду /help")

@dp.message_handler(commands=["help"])
async def help_com(message: types.Message):
    await message.reply("==========Команды для работы с БД==========\n"
                        "/add_db - создание или установка активной основной таблицы чата"
                        "/add_notifdb - создание таблиц уведомлений группы\n"
                        "/send_my_id - отправка ID пользователя админам\n"
                        "/reg_admin - регистрация админов\n"
                        "/add_to_db - добавление пользователя в таблицу\n"
                        "/edit_chat_db - вызов возможных команд для редактирования таблицы\n"
                        "/delete_from_db - удаление пользователя из таблицы\n"
                        "/delete_from_admin_db - удаление админа из таблицы\n"
                        "/delete_db - удаление таблицы чата\n"
                        "/delete_notif_db - удаление таблиц уведомлениё й\n"
                        "/delete_admin_db - удаление таблицы админов чата\n"
                        "==========Команды для работы с уведомлениями==========\n"
                        "/add_everyday_notif - создание ежедневных уведомлений\n"
                        "/remeverydaysch - удаление ежедневных уведомления\n"
                        "/add_everyweek_notif - создание еженедельных уведомлений\n"
                        "/start_birthday - создание рассылки напоминаний о ДР\n"
                        "/remove_birthday_notif - удаление уведомления о ДР\n"
                        "/start_vacation - создание рассылки напоминаний об отпусках\n"
                        "/remove_vacation_notif - удаление уведомления об отпусках\n"
                        "/show_all_birthday - вывод всех пользователей, подписанных на уведомления о ДР\n"
                        "/show_all_vacation - вывод всех пользователей, подписанных на уведомления об отпусках\n"
                        "/remeveryweeksch - удаление еженедельных уведомлений\n"
                        "/add_everymonth_notif - создание ежемесячных уведомлений\n"
                        "/remeverymounthsch - удаление ежемесячных уведомлений\n"
                        "/edit_notif_settings - настройка подписки и отписки на уведомления о ДР и отпусках(для всех пользователей)\n"
                        "==========Команды для работы с опросами==========\n"
                        "/vote - вывод всех команд для взаимодействия с опросами\n"
                        "/remove_vote - удаление опросов")

# whw - переменная,имеющая значение +неделю, от текущей даты
whw = arrow.utcnow().shift(weeks=1)

# Отправка ID пользователя админу
@dp.message_handler(commands=["send_my_id"])
async def start_command(message: types.Message):
    global listofadmins
    chat_id = message.chat.id
    user_id = message.from_user.id
    usrname = message.from_user.username
    await message.reply("Спасибо! Данные отправлены админам!")
    for i in listofadmins:
        await bot.send_message(i, f"ID пользователя @{usrname}: {user_id}")

# Создание таблицы с подписками на уведы
class addnotifdb(StatesGroup):
    addnotdb = State()

@dp.message_handler(commands=["add_notifdb"], state="*")
async def start_command(message: types.Message, state: FSMContext):
    global notifinchatid, everyday, everyweek, everymounth
    notifinchatid = "Notif" + chatdb
    everyday = "EveryDay" + chatdb
    everyweek = "EveryWeek" + chatdb
    everymounth = "EveryMounth" + chatdb
    await addnotifdb.addnotdb.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            try:
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {notifinchatid} (id Bigint UNIQUE, username VARCHAR(60) UNIQUE, birthdaynotif BOOLEAN, vacationnotif BOOLEAN )")
                await acur.execute(f"INSERT INTO {notifinchatid}(id, username) SELECT id, username FROM {chatdb}")
                await acur.execute(
                    f"UPDATE {notifinchatid} SET birthdaynotif = true, vacationnotif = true  ")
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {everyday} (tag VARCHAR(60) UNIQUE, text VARCHAR(60) UNIQUE, hours Bigint, minutes Bigint)")
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {everyweek} (tag VARCHAR(60) UNIQUE, text VARCHAR(60) UNIQUE, time VARCHAR(60), weekday Bigint)")
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {everymounth} (tag VARCHAR(60) UNIQUE, text VARCHAR(60) UNIQUE, time VARCHAR(60), mounthday Bigint)")
                await message.reply(f"Таблица уведомлений для {chatdb} успешно создана!")
            except:
                await message.reply(f"Таблица уведомлений для {chatdb} уже создана!")
    await state.finish()

async def adminreg(mes,adminlist, userid):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            try:
                await acur.execute(f"CREATE TABLE IF NOT EXISTS {adminlist} (id Bigint UNIQUE)")
                await acur.execute(
                    f"INSERT INTO {adminlist} (id) VALUES ({userid})")
                await bot.send_message(mes ,f"Админ добавлен в {adminlist}!")
            except:
                await bot.send_message(mes, f"Админ уже добавлен в таблицу {adminlist}")


class adreg(StatesGroup):
    regad = State()

@dp.message_handler(is_admin=True, commands='reg_admin', state="*")
async def process_add_db_command(message: types.Message, state: FSMContext):
    global chatdb
    global adminlist
    global listofadmins
    global chatlist
    mes = message.chat.id
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    adminlist = "admin" + chatdb
    userid = message.from_user.id
    listofadmins.append(userid)
    if message.chat.id in chatlist:
        pass
    if message.chat.id not in chatlist:
        chatlist.append(message.chat.id)
    await adreg.regad.set()
    await adminreg(mes,adminlist, userid)
    await state.finish()


async def addtodb(chatdb, userid, username, fio, birthday, vacation_start, vacation_end, notifinchatid):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {chatdb} (id,username, fio, birthday, vacation_start, vacation_end) VALUES ({userid},{username}, {fio}, {birthday}, {vacation_start}, {vacation_end})")
            await acur.execute(
                f"INSERT INTO {notifinchatid} (id,username) VALUES ({userid},{username})")
            await acur.execute(
                f"UPDATE {notifinchatid} SET birthdaynotif = true, vacationnotif = true WHERE username = {username} ")


class ad1(StatesGroup):
    ad = State()
    ad1 = State()


@dp.message_handler(commands="add_to_db", state="*")
async def showbd(message, state: FSMContext):
    global adminlist
    global chatdb
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text=f'Вы добавляете пользователя в таблицу {chatdb}')
                await message.answer(
                        "Введите данные username, id, ФИО, ДР и отпуска пользователя в таком формате:\n@nekochort\n466280885\nШорников Никита Сергеевич\n27.10\n26.12.2021\n28.01.2022")
                await state.finish()
                await ad1.ad1.set()
            listofadmins.clear()


@dp.message_handler(state=ad1.ad1, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    global notifinchatid
    notifinchatid = "Notif" + chatdb
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
        await addtodb(chatdb, userid, username, fio, birthday, vacation_start, vacation_end,
                      notifinchatid)
        await message.reply(f"Данные о пользователе {username} занесены в таблицу {chatdb}")
    except:
        await message.reply("Проверьте данные!")
    await state.finish()


async def adddb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"CREATE TABLE IF NOT EXISTS {chatdb} (id Bigint UNIQUE, username VARCHAR(60) UNIQUE, fio VARCHAR(60), birthday VARCHAR(60),vacation_start VARCHAR(60), vacation_end VARCHAR(60))")


class addchatdb(StatesGroup):
    adddb = State()


@dp.message_handler(is_admin=True, commands='add_db', state="*")  # Создние таблицы чата
async def process_add_db_command(message: types.Message, state: FSMContext):
    global chatdb
    global listofadmins
    global chatlist
    chatid = message,
    adid = message.from_user.id
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    chatlist.append(message.chat.id)
    await addchatdb.adddb.set()
    await adddb(chatdb)
    await message.reply(f"Таблица {chatdb} успешно создана! Прошу админа перейти в ЛС!")
    await state.finish()


async def deletedb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {chatdb}")


class ad2(StatesGroup):
    ad = State()


@dp.message_handler(commands="delete_db", state="*")
async def delbd(message, state: FSMContext):
    global adminlist
    global chatdb
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad2.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await deletedb(chatdb)
                await message.reply(f"Таблица {chatdb} успешно удалена!")
        listofadmins.clear()
    await state.finish()


async def deletnotifdb(chatdb, mes):
    notifinchatid = "Notif" + chatdb
    everyday = "EveryDay" + chatdb
    everyweek = "EveryWeek" + chatdb
    everymounth = "EveryMounth" + chatdb
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            try:
                await acur.execute(f"DROP TABLE {notifinchatid}")
                await acur.execute(f"DROP TABLE {everyday}")
                await acur.execute(f"DROP TABLE {everyweek}")
                await acur.execute(f"DROP TABLE {everymounth}")
            except:
                await message.Message.reply("Проверь данные")

class ad3(StatesGroup):
    ad = State()

@dp.message_handler(commands="delete_notif_db", state="*")
async def delbd(message, state: FSMContext):
    global adminlist
    global chatdb
    global listofadmins
    mes = message.chat.id
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad3.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                notifinchatid = "Notif" + chatdb
                await deletnotifdb(chatdb, mes)
                await message.reply(f"Таблица {notifinchatid} успешно удалена!")
        listofadmins.clear()
    await state.finish()


async def delformdb(chatdb, notifinchatid, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DELETE FROM {chatdb} WHERE username = {username}")
            await acur.execute(f"DELETE FROM {notifinchatid} WHERE username = {username}")


class ad4(StatesGroup):
    ad = State()
    ad1 = State()


@dp.message_handler(commands="delete_from_db", state="*")
async def delfdb(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad4.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text=f'Вы удаляете данные из таблицы {chatdb}')
                await message.answer("Введите username пользователя, которого хотите удалить из таблицы")
                await state.finish()
                await ad4.ad1.set()
        listofadmins.clear()

@dp.message_handler(state=ad4.ad1, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global chatdb
    send = message.text
    ls = send.split("\n", 5)
    username = ls[0]
    username = "'" + username + "'"
    await delformdb(chatdb, notifinchatid, username)
    await message.reply(f"Пользователь {username} удалён из таблицы!")
    await state.finish()


class edchdb(StatesGroup):
    editdb = State()

# Команда вызова команд для редактирвания основной БД чата
@dp.message_handler(commands=['edit_chat_db'], state="*")
async def edit_command(message: types.Message, state: FSMContext):
    await edchdb.editdb.set()
    await message.reply(
        "Выберите нужные команды и отправьте в личные сообщения боту:\n1)/edit_username - редактирование username пользователя\n2)/edit_fio - редактирование ФИО\n3)/edit_birthday - редактирование дней рождений\n4)/edit_vacation - редактирование дат отпусков")
    await state.finish()

# Редактирование username
async def username_red(chatdb, newusername,notifinchatid, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"UPDATE {chatdb} SET username = {newusername} WHERE username = {username}")
            await acur.execute(f"UPDATE {notifinchatid} SET username = {newusername} WHERE username = {username}")

class ad5(StatesGroup):
    ad = State()
    ad1 = State()

@dp.message_handler(commands="edit_username", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad5.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(f'Вы собираетесь изменить username пользвателя из таблицы {chatdb}')
                await message.answer("Введите username пользователя, а также устанавливаемый username")
                await state.finish()
                await ad5.ad1.set()
        listofadmins.clear()


@dp.message_handler(state=ad5.ad1, content_types=types.ContentTypes.TEXT)
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
        await username_red(chatdb,newusername,notifinchatid, username)
        await message.reply(f"Username пользователя {username} изменён в таблице {chatdb}")
    except:
        await message.reply("Проверьте данные!")
    await state.finish()

# Редактирование ФИО
async def fio_red(chatdb, newfio, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"UPDATE {chatdb} SET fio = {newfio} WHERE username = {username}")

async def deletedb(chatdb):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {chatdb}")


class ad2(StatesGroup):
    ad = State()


@dp.message_handler(commands="delete_db", state="*")
async def delbd(message, state: FSMContext):
    global adminlist
    global chatdb
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad2.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await deletedb(chatdb)
                await message.reply(f"Таблица {chatdb} успешно удалена!")
        listofadmins.clear()
    await state.finish()

class ad6(StatesGroup):
    ad = State()
    ad1 = State()


@dp.message_handler(commands="edit_fio", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad6.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(f'Вы собираетесь изменить ФИО пользвателя из таблицы {chatdb}')
                await message.answer("Введите username пользователя, а также ФИО, которое нужно установить")
                await state.finish()
                await ad6.ad1.set()
        listofadmins.clear()


@dp.message_handler(state=ad6.ad1, content_types=types.ContentTypes.TEXT)
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
        await message.reply("Проверьте данные!")
    await state.finish()

# Редактирование ДР
async def dr_red(chatdb, newbirthday, username):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"UPDATE {chatdb} SET birthday = {newbirthday} WHERE username = {username}")

class ad7(StatesGroup):
    ad = State()
    ad1 = State()


@dp.message_handler(commands="edit_birthday", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad7.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(f'Вы собираетесь изменить день рождения пользвателя из таблицы {chatdb}')
                await message.answer("Введите username пользователя, а также устанавливаемую дату дня рождения")
                await state.finish()
                await ad7.ad1.set()
        listofadmins.clear()

@dp.message_handler(state=ad7.ad1, content_types=types.ContentTypes.TEXT)
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
        await message.reply("Проверьте данные!")
    await state.finish()

# Редактирвание отпусков
async def vac_red(chatdb, newvacationstart, newvacationend, username):
    try:
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(
                    f"UPDATE {chatdb} SET vacation_start = {newvacationstart} WHERE username = {username}")
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"UPDATE {chatdb} SET vacation_end = {newvacationend} WHERE username = {username}")
    except:
        pass

class ad8(StatesGroup):
    ad = State()
    ad1 = State()

@dp.message_handler(commands="edit_vacation", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad8.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(f'Вы собираетесь изменить отпуска пользвателя из таблицы {chatdb}')
                await message.answer(
                        "Введите username пользователя, а также устанавливаемые даты начала и конца отпуска")
                await state.finish()
                await ad8.ad1.set()
        listofadmins.clear()

@dp.message_handler(state=ad8.ad1, content_types=types.ContentTypes.TEXT)
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
        await message.reply("Проверьте данные!")
    await state.finish()

class ad9(StatesGroup):
    ad = State()
    ad1 = State()

@dp.message_handler(commands="show_all_birthday", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad9.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                global notifinchatid
                notifinchatid = "Notif" + chatdb
                await message.reply("Вывожу всех пользователей, подписанных на рассылку о ДР")
                await ad9.ad1.set()
                async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                    async with aconn.cursor() as acur:
                        await acur.execute(f"SELECT username FROM {notifinchatid} WHERE birthdaynotif = true")
                        rec = await acur.fetchall()
                        for row in rec:
                            await message.answer(row[0])
                await state.finish()
        listofadmins.clear()
    await state.finish()

class bday(StatesGroup):
    times = State()
    times1 = ''
    theme = State()
    theme1 = ''
    tag = State()
    tag1 = ''
    name = State()
    name1 = ''

@dp.message_handler(commands="start_birthday", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте время, в которое будет отправляться данное сообщение: ')
                await bday.times.set()

@dp.message_handler(state=bday.times, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    if not any(map(str.isdigit, message.text)) or len(message.text) < 4 or ':' not in message.text:
        await message.reply("Пожалуйста напишите время в требуемом формате")
        return
    bday.times1 = message.text
    await message.answer(text='Введите тэг напоминания')
    await bday.tag.set()

@dp.message_handler(state=bday.tag, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    bday.tag1 = message.text
    taglist.append(bday.tag1)
    await message.answer(text='Введите описание напоминания')
    await bday.name.set()

@dp.message_handler(state=bday.name, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    global notifinchatid
    bday.name1 = message.text
    tl = bday.times1.split(':')
    tag1 = "'" + bday.tag1 + "'"
    tag = bday.tag1
    dtnowbirthday = arrow.utcnow().format('DD.MM')
    dtplusweekbirthday = arrow.utcnow().shift(weeks=1)
    dtplusweekbirthday = dtplusweekbirthday.format("DD.MM")
    cav = "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everyday} (tag, hours, minutes) VALUES ({tag1}, {tl[0]}, {tl[1]})")
            await acur.execute(
                f"ALTER TABLE {notifinchatid} ADD COLUMN {tag} BOOLEAN")#ОПАНА
            await acur.execute(
                f"UPDATE {notifinchatid} SET {tag} = true")
    async def job():
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"SELECT id FROM {notifinchatid} WHERE birthdaynotif = true")
                ids = await acur.fetchall()
                for row1 in ids:
                    await acur.execute(f"SELECT username FROM {notifinchatid} WHERE {tag} = true")
                    usernames = await acur.fetchall()
                    for row2 in usernames:
                        await acur.execute(f"SELECT birthday FROM {chatdb} WHERE username = {cav + row2[0] + cav}")
                        birthdays = await acur.fetchall()
                        for row3 in birthdays:
                            if row3[0] == dtplusweekbirthday:
                                await bot.send_message(row1[0], f"Сегодня {dtnowbirthday}, значит, что через неделю, а именно {row3[0]}, ДР у {row2[0]}! <3")
    scheduler.add_job(job, 'cron', hour=int(tl[0]), minute=int(tl[1]), id=bday.tag1, name=bday.name1)
    notiflist.append(bday.tag1 + ' - ' + bday.name1)
    await message.answer("Напоминание установлено.")
    await state.finish()

class delbirthday(StatesGroup):
    id = State()
    id1 = ''


@dp.message_handler(commands="remove_birthday_notif", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.answer("Выберите какое напоминание хотите удалить и введите его тэг: \n")
                m = ''
                for i in notiflist:
                    m += (i+'\n')
                await message.answer(m)
                await delbirthday.id.set()

@dp.message_handler(state=delbirthday.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    delnots.id1 = message.text
    if delnots.id1 not in taglist:
        await message.reply("Пожалуйста, проверьте список напоминаний и введите тэг ещё раз")
        return
    await removeshed(delnots.id1)
    for i in notiflist:
        if delnots.id1 in i.split(' - '):
            notiflist.remove(i)
            # taglist.remove(i)
            tag = "'" + delnots.id1 + "'"
            tag1 = delnots.id1
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everyday} WHERE tag = {tag}")
                    await acur.execute(
                        f"ALTER TABLE {notifinchatid} DROP COLUMN {tag1} CASCADE")
    await message.reply("Напоминание успешно удалено.")
    await state.finish()


class ad10(StatesGroup):
    ad = State()
    ad1 = State()

@dp.message_handler(commands="show_all_vacation", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad10.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                global notifinchatid
                notifinchatid = "Notif" + chatdb
                await message.reply("Вывожу всех пользователей, подписанных на рассылку об отпусках")
                await ad10.ad1.set()
                async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                    async with aconn.cursor() as acur:
                        await acur.execute(f"SELECT username FROM {notifinchatid} WHERE weekmeeting = true")
                        rec1 = await acur.fetchall()
                        for row in rec1:
                            await message.answer(row[0])
                await state.finish()
        listofadmins.clear()
    await state.finish()

class ad11(StatesGroup):
    ad = State()
    ad1 = State()

class vac(StatesGroup):
    times = State()
    times1 = ''
    theme = State()
    theme1 = ''
    tag = State()
    tag1 = ''
    name = State()
    name1 = ''

@dp.message_handler(commands="start_vacation", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.answer(text='Отправьте время, в которое будет отправляться данное сообщение: ')
                await vac.times.set()

@dp.message_handler(state=vac.times, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    if not any(map(str.isdigit, message.text)) or len(message.text) < 4 or ':' not in message.text:
        await message.reply("Пожалуйста напишите время в требуемом формате")
        return
    vac.times1 = message.text
    await message.answer(text='Введите тэг напоминания')
    await vac.tag.set()

@dp.message_handler(state=vac.tag, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    vac.tag1 = message.text
    taglist.append(vac.tag1)
    await message.answer(text='Введите описание напоминания')
    await vac.name.set()

@dp.message_handler(state=vac.name, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    global notifinchatid
    vac.name1 = message.text
    tl = vac.times1.split(':')
    tag1 = "'" + vac.tag1 + "'"
    tag = vac.tag1
    dtnowvacation = arrow.utcnow().format('DD.MM.YYYY')
    dtplusweekvacation = arrow.utcnow().shift(weeks=1)
    dtplusweekvacation = dtplusweekvacation.format("DD.MM.YYYY")
    cav = "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everyday} (tag, hours, minutes) VALUES ({tag1}, {tl[0]}, {tl[1]})")
            await acur.execute(
                f"ALTER TABLE {notifinchatid} ADD COLUMN {tag} BOOLEAN")
            await acur.execute(
                f"UPDATE {notifinchatid} SET {tag} = true")
    async def job():
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"SELECT id FROM {notifinchatid} WHERE vacationnotif = true")
                ids = await acur.fetchall()
                for row1 in ids:
                    await acur.execute(f"SELECT username FROM {notifinchatid} WHERE {tag} = true")
                    usernames = await acur.fetchall()
                    for row2 in usernames:
                        await acur.execute(f"SELECT vacation_start FROM {chatdb} WHERE username = {cav + row2[0] + cav}")
                        vacationstart = await acur.fetchall()
                        for row3 in vacationstart:
                           await acur.execute(
                                f"SELECT vacation_end FROM {chatdb} WHERE username = {cav + row2[0] + cav}")
                           vacationend = await acur.fetchall()
                           for row4 in vacationend:
                                if row3[0] == dtplusweekvacation:
                                    await bot.send_message(row1[0],
                                                     f"Сегодня {dtnowvacation}, значит, что через неделю, а именно {row3[0]}, начинается отпуск у {row2[0]}! Он продлится до {row4[0]} <3")
                                elif row4[0] == dtplusweekvacation:
                                    await bot.send_message(row1[0],
                                                     f"Сегодня {dtnowvacation}, значит, что через неделю, а именно {row4[0]}, заканчивается отпуск у {row2[0]}! Он начался {row3[0]} <3")
    scheduler.add_job(job, 'cron', hour=int(tl[0]), minute=int(tl[1]), id=vac.tag1, name=vac.name1)
    notiflist.append(vac.tag1 + ' - ' + vac.name1)
    await message.reply("Напоминание установлено.")
    await state.finish()

class delvac(StatesGroup):
    id = State()
    id1 = ''


@dp.message_handler(commands="remove_vacation_notif", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply("Выберите какое напоминание хотите удалить и введите его тэг: \n")
                m = ''
                for i in notiflist:
                    m += (i+'\n')
                await message.answer(m)
                await delvac.id.set()

@dp.message_handler(state=delvac.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    delnots.id1 = message.text
    if delnots.id1 not in taglist:
        await message.reply("Пожалуйста, проверьте список напоминаний и введите тэг ещё раз")
        return
    await removeshed(delnots.id1)
    for i in notiflist:
        if delnots.id1 in i.split(' - '):
            notiflist.remove(i)
            # taglist.remove(i)
            tag = "'" + delnots.id1 + "'"
            tag1 = delnots.id1
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everyday} WHERE tag = {tag}")
                    await acur.execute(
                        f"ALTER TABLE {notifinchatid} DROP COLUMN {tag1} CASCADE")
    await message.reply("Напоминание успешно удалено.")
    await state.finish()

async def deletadmedb(adminlist):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {adminlist}")

class ad13(StatesGroup):
    ad = State()


@dp.message_handler(is_admin = True, commands="delete_admin_db", state="*")
async def delbd(message, state: FSMContext):
    global adminlist
    global chatdb
    global listofadmins
    adminlist = "admin" + chatdb
    adid = message.from_user.id
    await ad2.ad.set()
    await deletadmedb(adminlist)
    await message.reply(f"Таблица {adminlist} успешно удалена!")
    listofadmins.clear()
    await state.finish()

async def delfromadmindb(adminlist, id):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DELETE FROM {adminlist} WHERE id = {id}")
            listofadmins.remove(id)

class ad14(StatesGroup):
    ad = State()
    ad1 = State()

@dp.message_handler(commands="delete_from_admin_db", state="*")
async def delfdb(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adminlist = "admin" + chatdb
    adid = message.from_user.id
    await ad14.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text=f'Вы удаляете данные из таблицы {adminlist}')
                await message.answer("Введите id админа, которого хотите удалить из таблицы")
                await state.finish()
                await ad14.ad1.set()
            else:
                await message.reply("Проверьте ввод!")
        listofadmins.clear()
@dp.message_handler(state=ad14.ad1, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global adminlist
    send = message.text
    ls = send.split("\n", 5)
    id = ls[0]
    await delfromadmindb(adminlist, id)
    await message.reply(f"Пользователь {id} удалён из таблицы {adminlist}!")
    await state.finish()


############### new every day notif ##################

class nedm(StatesGroup):
    times = State()
    times1 = ''
    theme = State()
    theme1 = ''
    tag = State()
    tag1 = ''
    name = State()
    name1 = ''


@dp.message_handler(commands="add_everyday_notif", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте время, в которое будет отправляться данное сообщение: ')
                await nedm.times.set()

@dp.message_handler(state=nedm.times, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    if not any(map(str.isdigit, message.text)) or len(message.text) < 4 or ':' not in message.text:
        await message.reply("Пожалуйста напишите время в требуемом формате")
        return
    nedm.times1 = message.text
    await message.answer(text='Отправьте текст для ежедневного уведомления: ')
    await nedm.theme.set()

@dp.message_handler(state=nedm.theme, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    nedm.theme1 = message.text
    await message.answer(text='Введите тэг напоминания')
    await nedm.tag.set()

@dp.message_handler(state=nedm.tag, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    nedm.tag1 = message.text
    taglist.append(nedm.tag1)
    await message.answer(text='Введите описание напоминания')
    await nedm.name.set()

@dp.message_handler(state=nedm.name, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    global notifinchatid
    nedm.name1 = message.text
    tl = nedm.times1.split(':')
    tag1 = "'" + nedm.tag1 +"'"
    tag = nedm.tag1
    text = "'" + nedm.theme1 + "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everyday} (tag,text, hours, minutes) VALUES ({tag1}, {text}, {tl[0]}, {tl[1]})")
            await acur.execute(
                f"ALTER TABLE {notifinchatid} ADD COLUMN {tag} BOOLEAN")
            await acur.execute(
                f"UPDATE {notifinchatid} SET {tag} = true")
    async def job():
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"SELECT id FROM {notifinchatid} WHERE {tag} = true")
                ids = await acur.fetchall()
                for row1 in ids:
                        await bot.send_message(row1[0], nedm.theme1)
    scheduler.add_job(job, 'cron', hour=int(tl[0]), minute=int(tl[1]), id=nedm.tag1, name=nedm.name1)
    notiflist.append(nedm.tag1 + ' - ' + nedm.name1)
    await message.reply("Напоминание установлено.")
    await state.finish()


############### delete everyday notif ########
class delnots(StatesGroup):
    id = State()
    id1 = ''


@dp.message_handler(commands="remeverydaysch", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply("Выберите какое напоминание хотите удалить и введите его тэг: \n")
                m = ''
                for i in notiflist:
                    m += (i+'\n')
                await message.answer(m)
                await delnots.id.set()

@dp.message_handler(state=delnots.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    delnots.id1 = message.text
    if delnots.id1 not in taglist:
        await message.reply("Пожалуйста, проверьте список напоминаний и введите тэг ещё раз")
        return
    await removeshed(delnots.id1)
    for i in notiflist:
        if delnots.id1 in i.split(' - '):
            notiflist.remove(i)
            # taglist.remove(i)
            tag = "'" + delnots.id1 + "'"
            tag1 = delnots.id1
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everyday} WHERE tag = {tag}")
                    await acur.execute(
                        f"ALTER TABLE {notifinchatid} DROP COLUMN {tag1} CASCADE")
    await message.reply("Напоминание успешно удалено.")
    await state.finish()

################### new every week notif #################
class delnots1(StatesGroup):
    id = State()
    id1 = ''


class newm(StatesGroup):
    date = State()
    date1 = ''
    time1 = ''
    theme = State()
    theme1 = ''
    tag = State()
    tag1 = ''
    name = State()
    name1 = ''


@dp.message_handler(commands="add_everyweek_notif", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте день недели (0-6, понедельник-воскресенье соответствено) и время, в которое будет отправляться данное напоминание: \n'
                                              'Пример: \n2\n18:00\n\n'
                                              'Расшифровка: напоминание будет отправляться каждую среду в 18:00')
                await newm.date.set()

@dp.message_handler(state=newm.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 0 or int(dt[0]) > 6 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[1] or len(dt)<2:
        await message.reply("Пожалуйста напишите день и время в требуемом формате")
        return
    newm.date1 = dt[0]
    newm.time1 = dt[1]
    await message.answer(text='Отправьте текст для еженедельного напоминания: ')
    await newm.theme.set()

@dp.message_handler(state=newm.theme, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    newm.theme1 = message.text
    await message.answer(text='Введите тэг напоминания')
    await newm.tag.set()

@dp.message_handler(state=newm.tag, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    newm.tag1 = message.text
    taglist.append(newm.tag1)
    await message.answer(text='Введите описание напоминания')
    await newm.name.set()

@dp.message_handler(state=newm.name, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyweek
    global notifinchatid
    newm.name1 = message.text
    tl = newm.time1.split(':')
    tag = "'" + newm.tag1 + "'"
    tag1 = newm.tag1
    text = "'" + newm.theme1 + "'"
    date = "'" + newm.date1 + "'"
    time = "'" + newm.time1 + "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everyweek} (tag,text, time, weekday) VALUES ({tag}, {text}, {time}, {date})")
            await acur.execute(
                f"ALTER TABLE {notifinchatid} ADD COLUMN {tag1} BOOLEAN")
            await acur.execute(
                f"UPDATE {notifinchatid} SET {tag1} = true")
    async def job():
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"SELECT id FROM {notifinchatid} WHERE {tag1} = true")
                ids = await acur.fetchall()
                for row1 in ids:
                    await bot.send_message(row1[0], newm.theme1)
    scheduler.add_job(job, 'cron', day_of_week=int(newm.date1),  hour=int(tl[0]), minute=int(tl[1]), id=newm.tag1, name=newm.name1)
    notiflist.append(newm.tag1 + ' - ' + newm.name1)
    await message.reply("Напоминание установлено.")
    await state.finish()

@dp.message_handler(commands="remeveryweeksch", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply("Выберите какое напоминание хотите удалить и введите его тэг: \n")
                m = ''
                for i in notiflist:
                    m += (i+'\n')
                await message.answer(m)
                await delnots1.id.set()

@dp.message_handler(state=delnots1.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyweek
    delnots1.id1 = message.text
    if delnots1.id1 not in taglist:
        await message.reply("Пожалуйста, проверьте список напоминаний и введите тэг ещё раз")
        return
    await removeshed(delnots1.id1)
    for i in notiflist:
        if delnots1.id1 in i.split(' - '):
            notiflist.remove(i)
            # taglist.remove(i)
            tag = "'" + delnots1.id1 + "'"
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everyweek} WHERE tag = {tag}")
                    await acur.execute(
                        f"ALTER TABLE {notifinchatid} DROP COLUMN {tag} CASCADE")
    await message.reply("Напоминание успешно удалено.")
    await state.finish()


############## new every mon notif ################
class delnots2(StatesGroup):
    id = State()
    id1 = ''


class nemm(StatesGroup):
    date = State()
    date1 = ''
    time1 = ''
    theme = State()
    theme1 = ''
    tag = State()
    tag1 = ''
    name = State()
    name1 = ''


@dp.message_handler(commands="add_everymonth_notif", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте день месяца и время, в которое будет отправляться данное напоминание: \n'
                                              'Пример: \n28\n18:00\n\n'
                                              'Расшифровка: напоминание будет отправляться каждый месяц 28 числа в 18:00')
                await nemm.date.set()

@dp.message_handler(state=nemm.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 1 or int(dt[0]) > 31 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[1] or len(dt)<2:
        await message.reply("Пожалуйста, напишите дату и время в требуемом формате")
        return
    nemm.date1 = dt[0]
    nemm.time1 = dt[1]
    await message.answer(text='Отправьте текст для ежемесячного напоминания: ')
    await nemm.theme.set()

@dp.message_handler(state=nemm.theme, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    nemm.theme1 = message.text
    await message.answer(text='Введите тэг напоминания')
    await nemm.tag.set()

@dp.message_handler(state=nemm.tag, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    nemm.tag1 = message.text
    taglist.append(nemm.tag1)
    await message.answer(text='Введите описание напоминания')
    await nemm.name.set()

@dp.message_handler(state=nemm.name, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everymounth
    global notifinchatid
    global notiflist
    global taglist
    nemm.name1 = message.text
    tl = nemm.time1.split(':')
    tag = "'" + nemm.tag1 + "'"
    tag1 = nemm.tag1
    text = "'" + nemm.theme1 + "'"
    date = "'" + nemm.date1 + "'"
    time = "'" + nemm.time1 + "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everymounth} (tag,text, time, mounthday) VALUES ({tag}, {text}, {time}, {date})")
            await acur.execute(
                f"ALTER TABLE {notifinchatid} ADD COLUMN {tag1} BOOLEAN")
            await acur.execute(
                f"UPDATE {notifinchatid} SET {tag1} = true")
    async def job():
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"SELECT id FROM {notifinchatid} WHERE {tag1} = true")
                ids = await acur.fetchall()
                for row1 in ids:
                        await bot.send_message(row1[0], nemm.theme1)

    scheduler.add_job(job, 'cron', day=int(nemm.date1), hour=int(tl[0]), minute=int(tl[1]), id=nemm.tag1,
                      name=nemm.name1)
    notiflist.append(nemm.tag1 + ' - ' + nemm.name1)
    taglist.append(nemm.tag1)
    await message.reply("Напоминание установлено.")
    await state.finish()

@dp.message_handler(commands="remeverymounthsch", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.answer("Выберите какое напоминание хотите удалить и введите его тэг: \n")
                m = ''
                for i in notiflist:
                    m += (i+'\n')
                await message.answer(m)
                await delnots2.id.set()

@dp.message_handler(state=delnots2.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everymounth
    global notifinchatid
    delnots2.id1 = message.text
    if delnots2.id1 not in taglist:
        await message.reply("Пожалуйста, проверьте список напоминаний и введите тэг ещё раз")
        return
    await removeshed(delnots2.id1)
    for i in notiflist:
        if delnots2.id1 in i.split(' - '):
            notiflist.remove(i)
            # taglist.remove(i)
            tag = "'" + delnots2.id1 + "'"
            tag1 = delnots2.id1
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everymounth} WHERE tag = {tag}")
                    await acur.execute(
                        f"ALTER TABLE {notifinchatid} DROP COLUMN {tag1} CASCADE")
    #
    await message.reply("Напоминание успешно удалено.")
    await state.finish()


###############################

class edit(StatesGroup):
    state = State()
    state2 = State()
    state3 = State()
    state4 = State()
    state5 = State()

button1 = KeyboardButton('День рождения')
button2 = KeyboardButton('Отпуска')

@dp.message_handler(commands="edit_notif_settings", state="*")
async def menu(message: types.Message, state: FSMContext):
    start_menu = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True).add(
    button1).add(button2)
    await message.reply("Выберите уведомление на которое хотите изменить подписку",
                           reply_markup=start_menu)
    await edit.state.set()


@dp.message_handler(state=edit.state, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    if message.text == "День рождения":
        source_menu = types.ReplyKeyboardMarkup(
            row_width=3, resize_keyboard=True, one_time_keyboard=True)
        source_menu.add("Подписаться", "Отписаться")
        source_menu.add("Назад")
        await bot.send_message(
            message.chat.id, "Выберите вариант: ", reply_markup=source_menu
        )
        await edit.state2.set()

    elif message.text == "Отпуска":
        source_menu = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True, one_time_keyboard=True)
        source_menu.add(
            "Подписаться",
            "Отписаться",
        )
        source_menu.add("Назад")
        await bot.send_message(
            message.chat.id, "Выберите вариант: ", reply_markup=source_menu
        )
        await edit.state3.set()

@dp.message_handler(state=edit.state2, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    if message.text == "Отписаться":
        await bot.send_message(
            message.chat.id, "Вы отписались от уведомлений о Днях рождения"
        )
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(
                    f"UPDATE {notifinchatid} SET birthdaynotif = false WHERE id = {message.from_user.id}")

    elif message.text == "Подписаться":
        await bot.send_message(
            message.chat.id, "Вы подписались на уведомления о Днях рождения"
        )
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"UPDATE {notifinchatid} SET birthdaynotif = true WHERE id = {message.from_user.id}")
    elif message.text == "Назад":
        await menu(message)

@dp.message_handler(state=edit.state3, content_types=types.ContentTypes.TEXT)
async def age_step(message: types.Message, state: FSMContext):
    if message.text == "Отписаться":
        await bot.send_message(message.chat.id, "Вы отписались от уведомлений об отпусках")
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"UPDATE {notifinchatid} SET vacationnotif = false WHERE id = {message.from_user.id}")
    elif message.text == "Подписаться":
        await bot.send_message(message.chat.id, "Вы подписались на уведомления об отпусках")
        async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
            async with aconn.cursor() as acur:
                await acur.execute(f"UPDATE {notifinchatid} SET vacationnotif = true WHERE id = {message.from_user.id}")
    elif message.text == "Назад":
        await menu(message)

@dp.message_handler(commands="vote", state="*")
async def showbd(message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='/send_now_vote - голосование отправится сразу без ограничения по времени\n'
                                             '/send_now_vote_ogrvr - голосование отправится сразу c ограничения по времени\n'
                                             '/everyday_vote - голосование будет отправляться каждый день без ограничения по времени\n'
                                             '/everyday_vote_ogr - голосование будет отправляться каждый день с ограничением по времени\n'
                                             '/everyweek_vote - голосование будут отправляться каждую неделю без ограничения по времени\n'
                                             '/everyweek_vote_ogr - голосование будут отправляться каждую неделю с ограничением по времени\n'
                                             '/everymonth_vote - голосование будут отправляться каждый месяц без ограничения по времени\n'
                                             '/everymonth_vote_ogr - голосование будут отправляться каждый месяц с ограничением по времени\n')

class vote1(StatesGroup):
    time = State()
    time1 = ' '
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''

@dp.message_handler(commands="everyday_vote", state="*")
async def evD_vote(message, state: FSMContext):
    await message.answer(text='Отправьте время, когда будет отпраляться голосование')
    await vote1.time.set()

@dp.message_handler(state=vote1.time, content_types=types.ContentType.TEXT)
async def evD_vote1_time(message: types.Message, state: FSMContext):
    if not any(map(str.isdigit, message.text)) or len(message.text) < 4 or ':' not in message.text:
        await message.reply('Пожалуйста, напишите время в требуемом формате')
        return
    vote1.time1 = message.text
    await message.answer(text='Отправьте тему голосования')
    await vote1.vote_theme.set()

@dp.message_handler(state=vote1.vote_theme, content_types=types.ContentType.TEXT)
async def evD_vote1_tema(message: types.Message, state: FSMContext):
    vote1.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote1.var.set()

@dp.message_handler(state=vote1.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    vote1.var1 = message.text.split('\n')
    tl = vote1.time1.split(':')
    async def job():
        for i in chatlist:
            await bot.send_poll(i, vote1.them, options=vote1.var1, is_anonymous=False)
    scheduler.add_job(job, 'cron', hour=int(tl[0]), minute=int(tl[1]))
    await message.reply("Голосование установлено")
    await state.finish()


class vote12(StatesGroup):
    time = State()
    time1 = ' '
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''
    ogr = State()
    ogr1 = ''

@dp.message_handler(commands="everyday_vote_ogr", state="*")
async def evD_vote(message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте время, в которое будет отпраляться голосование')
                await vote12.time.set()

@dp.message_handler(state=vote12.time, content_types=types.ContentType.TEXT)
async def evD_vote1_time(message: types.Message, state: FSMContext):
    if not any(map(str.isdigit, message.text)) or len(message.text) < 4 or ':' not in message.text:
        await message.reply('Пожалуйста, напишите время в требуемом формате')
        return
    vote12.time1 = message.text
    await message.answer(text='Введите время на голосование в минутах (до 10)')
    await vote12.ogr.set()

@dp.message_handler(state=vote12.ogr, content_types=types.ContentType.TEXT)
async def sn_vote(message, state: FSMContext):
    vote12.ogr1 = message.text
    await message.answer(text='Введите тему голосования')
    await vote12.vote_theme.set()

@dp.message_handler(state=vote12.vote_theme, content_types=types.ContentType.TEXT)
async def evD_vote1_tema(message: types.Message, state: FSMContext):
    vote12.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote12.var.set()

@dp.message_handler(state=vote12.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    vote12.var1 = message.text.split('\n')
    tl = vote12.time1.split(':')
    global everyday
    global notifinchatid
    global taglist
    global notiflist
    tag1 = "'" + vote12.tag1 + "'"
    tag = vote12.tag1
    cav = "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"ALTER TABLE {notifinchatid} ADD COLUMN {tag} BOOLEAN")  # ОПАНА
            await acur.execute(
                f"UPDATE {notifinchatid} SET {tag} = true")
    async def job():
        for i in chatlist:
            await bot.send_poll(i, vote12.them, options=vote12.var1, is_anonymous=False, open_period=int(vote12.ogr1)*60)
    scheduler.add_job(job, 'cron', hour=int(tl[0]), minute=int(tl[1]), id=vote12.tag1, name=vote12.name1)
    notiflist.append(vote12.tag1 + ' - ' + vote12.name1)
    taglist.append(vote12.tag1)
    await message.reply("Голосование установлено")
    await state.finish()

class vote2(StatesGroup):
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''

@dp.message_handler(commands="send_now_vote", state="*")
async def sn_vote(message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                global chatlist
                await message.answer(text='Отправьте тему голосования')
                await vote2.vote_theme.set()

@dp.message_handler(state=vote2.vote_theme, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    vote2.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote2.var.set()

@dp.message_handler(state=vote2.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    global chatlist
    vote2.var1 = message.text.split('\n')
    for i in chatlist:
        await bot.send_poll(i, vote2.them, options=vote2.var1, is_anonymous=False)
    await state.finish()


class vote2_2(StatesGroup):
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''
    ogr = State()
    ogr1 = ''

@dp.message_handler(commands="send_now_vote_ogrvr", state="*")
async def sn_vote(message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Введите время на голосование в минутах (до 10)')
                await vote2_2.ogr.set()

@dp.message_handler(state=vote2_2.ogr, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    vote2_2.ogr1 = message.text
    await message.answer(text='Отправьте тему голосования')
    await vote2_2.vote_theme.set()

@dp.message_handler(state=vote2_2.vote_theme, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    vote2_2.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote2_2.var.set()

@dp.message_handler(state=vote2_2.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    vote2_2.var1 = message.text.split('\n')
    for i in chatlist:
        await bot.send_poll(i, vote2_2.them, options=vote2_2.var1, is_anonymous=False, open_period=int(vote2_2.ogr1)*60)
    await state.finish()

class vote3(StatesGroup):
    time = State()
    time1 = ' '
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''
    date = State()
    date1 = ''


@dp.message_handler(commands="everyweek_vote", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте день недели (0-6, понедельник-воскресенье соответствено) и время, в которое будет отправляться голосование: \n'
                                              'Пример: \n2\n18:00\n\n'
                                              'Расшифровка: голосование будет отправляться каждую среду в 18:00')
                await vote3.tag.set()

@dp.message_handler(state=vote3.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 0 or int(dt[0]) > 6 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[1] or len(dt)<2:
        await message.reply("Пожалуйста напишите дату и время в требуемом формате")
        return
    vote3.date1 = dt[0]
    vote3.time1 = dt[1]
    await message.answer(text='Отправьте тему голосования: ')
    await vote3.vote_theme.set()

@dp.message_handler(state=vote3.vote_theme, content_types=types.ContentType.TEXT)
async def evD_vote1_tema(message: types.Message, state: FSMContext):
    vote3.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote3.var.set()

@dp.message_handler(state=vote3.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    global taglist
    global notiflist
    vote3.var1 = message.text.split('\n')
    tl = vote3.time1.split(':')
    async def job():
        for i in chatlist:
            await bot.send_poll(i, vote3.them, options=vote3.var1, is_anonymous=False)
    scheduler.add_job(job, 'cron', day_of_week=int(vote3.date1), hour=int(tl[0]), minute=int(tl[1]), id=vote3.tag1, name=vote3.name1)
    notiflist.append(vote3.tag1 + ' - ' + vote3.name1)
    taglist.append(vote3.tag1)
    await message.reply("Голосование установлено")
    await state.finish()

class vote32(StatesGroup):
    time = State()
    time1 = ' '
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''
    date = State()
    date1 = ''
    ogr = State()
    ogr1 = ''

@dp.message_handler(commands="everyweek_vote_ogr", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте день недели (0-6, понедельник-воскресенье соответствено) и время, в которое будет отправляться голосование: \n'
                                              'Пример: \n2\n18:00\n\n'
                                              'Расшифровка: голосование будет отправляться каждую среду в 18:00')
                await vote32.date.set()

@dp.message_handler(state=vote32.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 0 or int(dt[0]) > 6 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[1] or len(dt)<2:
        await message.reply("Пожалуйста, напишите дату и время в требуемом формате")
        return
    vote32.date1 = dt[0]
    vote32.time1 = dt[1]
    await message.answer(text='Введите время на голосование в минутах (до 10)')
    await vote32.ogr.set()

@dp.message_handler(state=vote32.ogr, content_types=types.ContentType.TEXT)
async def sn_vote(message, state: FSMContext):
    vote32.ogr1 = message.text
    await message.answer(text='Введите тему голосования')
    await vote32.vote_theme.set()

@dp.message_handler(state=vote32.vote_theme, content_types=types.ContentType.TEXT)
async def evD_vote1_tema(message: types.Message, state: FSMContext):
    vote32.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote32.var.set()

@dp.message_handler(state=vote32.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    global notiflist
    global taglist
    vote32.var1 = message.text.split('\n')
    tl = vote32.time1.split(':')
    async def job():
        for i in chatlist:
            await bot.send_poll(i, vote32.them, options=vote32.var1, is_anonymous=False, open_period=int(vote32.ogr1)*60)
    scheduler.add_job(job, 'cron', day_of_week=int(vote32.date1), hour=int(tl[0]), minute=int(tl[1]), id=vote32.tag1, name=vote32.name1)
    notiflist.append(vote32.tag1 + ' - ' + vote32.name1)
    taglist.append(vote32.tag1)
    await message.answer("Голосование установлено")
    await state.finish()


class vote4(StatesGroup):
    time = State()
    time1 = ' '
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''
    date = State()
    date1 = ''


@dp.message_handler(commands="everymonth_vote", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте день месяца и время, в которое будет отправляться голосование: \n'
                                              'Пример: \n28\n18:00\n\n'
                                              'Расшифровка: голосование будет отправляться каждый месяц 28 числа в 18:00')
                await vote4.tag.set()

@dp.message_handler(state=vote4.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 1 or int(dt[0]) > 31 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[
        1] or len(dt) < 2:
        await message.reply("Пожалуйста, напишите дату и время в требуемом формате")
        return
    vote4.date1 = dt[0]
    vote4.time1 = dt[1]
    await message.answer(text='Отправьте тему голосования: ')
    await vote4.vote_theme.set()

@dp.message_handler(state=vote4.vote_theme, content_types=types.ContentType.TEXT)
async def evD_vote1_tema(message: types.Message, state: FSMContext):
    vote4.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote4.var.set()

@dp.message_handler(state=vote4.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    global notiflist
    global taglist
    vote4.var1 = message.text.split('\n')
    tl = vote4.time1.split(':')
    async def job():
        for i in chatlist:
            await bot.send_poll(i, vote4.them, options=vote4.var1, is_anonymous=False)
    scheduler.add_job(job, 'cron', day=int(vote4.date1), hour=int(tl[0]), minute=int(tl[1]), id=vote4.tag1, name=vote4.name1)
    notiflist.append(vote4.tag1 + ' - ' + vote4.name1)
    taglist.append(vote4.tag1)
    await message.reply("Голосование установлено")
    await state.finish()

class vote42(StatesGroup):
    time = State()
    time1 = ' '
    vote_theme = State()
    var = State()
    var1 = ''
    them = ''
    date = State()
    date1 = ''
    ogr = State()
    ogr1 = ''

@dp.message_handler(commands="everymonth_vote_ogr", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.reply(text='Отправьте день месяца и время, в которое будет отправляться голосование: \n'
                                              'Пример: \n28\n18:00\n\n'
                                              'Расшифровка: голосование будет отправляться каждый месяц 28 числа в 18:00')
                await vote42.date.set()

@dp.message_handler(state=vote42.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 1 or int(dt[0]) > 31 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[
        1] or len(dt) < 2:
        await message.reply("Пожалуйста, напишите дату и время в требуемом формате")
        return
    vote42.date1 = dt[0]
    vote42.time1 = dt[1]
    await message.answer(text='Введите время на голосование в минутах (до 10): ')
    await vote42.ogr.set()

@dp.message_handler(state=vote42.ogr, content_types=types.ContentType.TEXT)
async def sn_vote(message, state: FSMContext):
    vote42.ogr1 = message.text
    await message.answer(text='Введите тему голосования')
    await vote42.vote_theme.set()

@dp.message_handler(state=vote42.vote_theme, content_types=types.ContentType.TEXT)
async def evD_vote1_tema(message: types.Message, state: FSMContext):
    vote42.them = message.text
    await message.answer(text='Введите варианты голосования, каждый в отдельной строке')
    await vote42.var.set()

@dp.message_handler(state=vote42.var, content_types=types.ContentType.TEXT)
async def sn_vote2(message: types.Message, state: FSMContext):
    global notiflist
    global taglist
    vote42.var1 = message.text.split('\n')
    tl = vote42.time1.split(':')
    async def job():
        for i in chatlist:
            await bot.send_poll(i, vote42.them, options=vote42.var1, is_anonymous=False, open_period=int(vote42.ogr1)*60)
    scheduler.add_job(job, 'cron', day=int(vote42.date1), hour=int(tl[0]), minute=int(tl[1]), id=vote42.tag1, name=vote42.name1)
    notiflist.append(vote42.tag1 + ' - ' + vote42.name1)
    taglist.append(vote42.tag1)
    await message.reply("Голосование установлено")
    await state.finish()

class delvote(StatesGroup):
    id = State()
    id1 = ''

@dp.message_handler(commands="remove_vote", state="*")
async def name_step(message: types.Message, state: FSMContext):
    global adminlist
    global listofadmins
    adid = message.from_user.id
    adminlist = "admin" + chatdb
    await ad1.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
            if adid in listofadmins:
                await message.answer("Выберите какое напоминание хотите удалить и введите его тэг: \n")
                m = ''
                for i in notiflist:
                    m += (i+'\n')
                await message.answer(m)
                await delvote.id.set()

@dp.message_handler(state=delvote.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everyday
    delnots.id1 = message.text
    if delnots.id1 not in taglist:
        await message.reply("Пожалуйста, проверьте список напоминаний и введите тэг ещё раз")
        return
    await removeshed(delnots.id1)
    for i in notiflist:
        if delnots.id1 in i.split(' - '):
            notiflist.remove(i)
            # taglist.remove(i)
            tag = "'" + delnots.id1 + "'"
            tag1 = delnots.id1
    await message.reply("Напоминание успешно удалено.")
    await state.finish()

scheduler.start()

if __name__ == '__main__':
    executor.start_polling(dp)
