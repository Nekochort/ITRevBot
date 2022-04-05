import asyncio
from asyncio import WindowsSelectorEventLoopPolicy

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.dispatcher.filters import state
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils import executor
import psycopg
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton, message
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import TOKEN, DB_URI

from aiogram.dispatcher.filters import BoundFilter


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
    timemanagment = birthdaynotif = weekmeeting = vacationnotif = True
    await addnotifdb.addnotdb.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            try:
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {notifinchatid} (id Bigint UNIQUE, username VARCHAR(60) UNIQUE, timemanagment BOOLEAN, birthdaynotif BOOLEAN, weekmeeting BOOLEAN, vacationnotif BOOLEAN )")
                await acur.execute(f"INSERT INTO {notifinchatid}(id, username) SELECT id, username FROM {chatdb}")
                await acur.execute(
                    f"UPDATE {notifinchatid} SET timemanagment = true,birthdaynotif = true, weekmeeting = true, vacationnotif = true  ")
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {everyday} (tag VARCHAR(60) UNIQUE, text VARCHAR(60) UNIQUE, hours Bigint, minutes Bigint)")
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {everyweek} (tag VARCHAR(60) UNIQUE, text VARCHAR(60) UNIQUE, time VARCHAR(60), weekday Bigint)")
                await acur.execute(
                    f"CREATE TABLE IF NOT EXISTS {everymounth} (tag VARCHAR(60) UNIQUE, text VARCHAR(60) UNIQUE, time VARCHAR(60), mounthday Bigint)")
            except:
                await message.answer(f"ХЬЮСТОН, У НАС ПРОБЛЕМЫ. Я ДОЛБАЁБ!")
        await message.answer(f"Таблица уведомлений для {chatdb} успешно создана!")
    await state.finish()


async def addc(mes,notifinchatid):
    test = "test"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            try:
                await acur.execute(
                    f"ALTER TABLE {notifinchatid} ADD COLUMN {test} BOOLEAN")
                await acur.execute(
                    f"UPDATE {notifinchatid} SET {test} = true")
            except:
                await bot.send_message(mes, "Та погоди ты!")


class addcol(StatesGroup):
    add = State()

@dp.message_handler(is_admin=True, commands='add_col', state="*")
async def process_add_db_command(message: types.Message, state: FSMContext):
    global notifinchatid
    mes = message.chat.id
    await addcol.add.set()
    await addc(mes,notifinchatid)
    await state.finish()


async def adminreg(mes,adminlist, userid):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"CREATE TABLE IF NOT EXISTS {adminlist} (id Bigint UNIQUE)")
            try:
                await acur.execute(
                    f"INSERT INTO {adminlist} (id) VALUES ({userid})")
                await message.reply(f"Админ добавлен в {adminlist}!")
            except:
                await bot.send_message(mes, "Ты уже добавлен в таблицу!")


class adreg(StatesGroup):
    regad = State()

@dp.message_handler(is_admin=True, commands='reg_admin', state="*")
async def process_add_db_command(message: types.Message, state: FSMContext):
    global chatdb
    global adminlist
    global listofadmins
    mes = message.chat.id
    chatdb = message.chat.id
    chatdb = str(chatdb)
    chatdb = chatdb.replace("-", "")
    chatdb = "group" + chatdb
    adminlist = "admin" + chatdb
    userid = message.from_user.id
    await adreg.regad.set()
    await adminreg(mes,adminlist, userid)
    print(listofadmins)
    await state.finish()


async def addtodb(chatdb, userid, username, fio, birthday, vacation_start, vacation_end, notifinchatid):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {chatdb} (id,username, fio, birthday, vacation_start, vacation_end) VALUES ({userid},{username}, {fio}, {birthday}, {vacation_start}, {vacation_end})")
            await acur.execute(
                f"INSERT INTO {notifinchatid} (id,username) VALUES ({userid},{username})")
            await acur.execute(
                f"UPDATE {notifinchatid} SET timemanagment = true,birthdaynotif = true, weekmeeting = true, vacationnotif = true WHERE username = {username} ")


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
                        "Введите данные о пользователе:\nПример:\nUsername: @nekochort\nID: 466280885\nФИО: Шорников Никита Сергеевич\nДень рождения: 27.10\nДата начала отпуска: 26.12.2021\nДата окончания отпуска: 28.01.2022")
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
        await message.answer("Проверьте данные!")
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
    adid = message.from_user.id
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
                await bot.send_message(mes, "Хьюстон, у нас проблмы...Проверь данные")


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
@dp.message_handler(is_admin=True, commands=['edit_chat_db'], state="*")
async def edit_command(message: types.Message, state: FSMContext):
    await edchdb.editdb.set()
    await message.answer(
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
                    await message.answer(f'Вы собираетесь изменить username пользвателя из таблицы {chatdb}')
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
        await message.answer("Проверьте данные!")
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
                    await message.answer(f'Вы собираетесь изменить ФИО пользвателя из таблицы {chatdb}')
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
        await message.answer("Проверьте данные!")
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
                    await message.answer(f'Вы собираетесь изменить день рождения пользвателя из таблицы {chatdb}')
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
        await message.answer("Проверьте данные!")
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
                    await message.answer(f'Вы собираетесь изменить отпуска пользвателя из таблицы {chatdb}')
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
        await message.answer("Проверьте данные!")
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

@dp.message_handler(commands="show_all_time", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adminlist = "admin" + chatdb
    adid = message.from_user.id
    await ad11.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
                if adid in listofadmins:
                    global notifinchatid
                    notifinchatid = "Notif" + chatdb
                    await message.reply("Вывожу всех пользователей, подписанных на рассылку о списании времени")
                    await ad11.ad1.set()
                    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                        async with aconn.cursor() as acur:
                            await acur.execute(f"SELECT username FROM {notifinchatid} WHERE timemanagment = true")
                            rec2 = await acur.fetchall()
                            for row in rec2:
                                await message.answer(row[0])
                                await state.finish()
            listofadmins.clear()
    await state.finish()

class ad12(StatesGroup):
    ad = State()
    ad1 = State()

@dp.message_handler(commands="show_all_weekmeeting", state="*")
async def edun(message, state: FSMContext):
    global adminlist
    global chatdb
    global notifinchatid
    global listofadmins
    adminlist = "admin" + chatdb
    adid = message.from_user.id
    await ad12.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
                if adid in listofadmins:
                    global notifinchatid
                    notifinchatid = "Notif" + chatdb
                    await message.reply("Вывожу всех пользователей, подписанных на рассылку о совещаниях")
                    await ad12.ad1.set()
                    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                        async with aconn.cursor() as acur:
                            await acur.execute(f"SELECT username FROM {notifinchatid} WHERE weekmeeting = true")
                            rec3 = await acur.fetchall()
                            for row in rec3:
                                await message.answer(row[0])
                    await state.finish()
            listofadmins.clear()
    await state.finish()

async def deletadmedb(adminlist):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DROP TABLE {adminlist}")


class ad13(StatesGroup):
    ad = State()


@dp.message_handler(commands="delete_admin_db", state="*")
async def delbd(message, state: FSMContext):
    global adminlist
    global chatdb
    global listofadmins
    adminlist = "admin" + chatdb
    adid = message.from_user.id
    await ad2.ad.set()
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"SELECT id FROM {adminlist}")
            rec = await acur.fetchall()
            for row in rec:
                listofadmins.append(row[0])
                if adid in listofadmins:
                    await deletadmedb(adminlist)
                    await message.reply(f"Таблица {adminlist} успешно удалена!")
            listofadmins.clear()
    await state.finish()

async def delfromadmindb(adminlist, id):
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(f"DELETE FROM {adminlist} WHERE id = {id}")
            await listofadmins.remove(id)


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
                print(listofadmins)
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


@dp.message_handler(commands="nedm", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.answer(text='Отправьте время, в которое будет отправляться данное сообщение: ')
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
    nedm.name1 = message.text
    tl = nedm.times1.split(':')
    tag = "'" + nedm.tag1 +"'"
    text = "'" + nedm.theme1 + "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everyday} (tag,text, hours, minutes) VALUES ({tag}, {text}, {tl[0]}, {tl[1]})")
    async def job():
        await bot.send_message(message.from_user.id, nedm.theme1)
    scheduler.add_job(job, 'cron', hour=int(tl[0]), minute=int(tl[1]), id=nedm.tag1, name=nedm.name1)
    notiflist.append(nedm.tag1 + ' - ' + nedm.name1)
    await message.answer("Напоминание установлено.")
    print(nedm.times1, ' ', nedm.theme1, ' ', nedm.tag1)
    print(notiflist)
    await state.finish()


############### delete everyday notif ########
class delnots(StatesGroup):
    id = State()
    id1 = ''


@dp.message_handler(commands="remeverydaysch", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.answer("Выберите какое напоминание хотите удалить и введите его тэг: \n")
    m = ''
    for i in notiflist:
        m += (i+'\n')
    await message.answer(m)
    print(notiflist)
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
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everyday} WHERE tag = {tag}")
    await message.reply("Напоминание успешно удалено.")
    print(notiflist)
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


@dp.message_handler(commands="newm", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.answer(text='Отправьте день недели (0-6, понедельник-воскресенье соответствено) и время, в которое будет отправляться данное напоминание: \n'
                              'Пример: \n2\n18:00\n\n'
                              'Расшифровка: напоминание будет отправляться каждую среду в 18:00')
    await newm.date.set()

@dp.message_handler(state=newm.date, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    dt = message.text.split('\n')
    if int(dt[0]) < 0 or int(dt[0]) > 6 or not any(map(str.isdigit, dt[1])) or len(dt[1]) < 4 or ':' not in dt[1] or len(dt)<2:
        await message.reply("Пожалуйста напишите дату и время в требуемом формате")
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
    newm.name1 = message.text
    tl = newm.time1.split(':')
    tag = "'" + newm.tag1 + "'"
    text = "'" + newm.theme1 + "'"
    date = "'" + newm.date1 + "'"
    time = "'" + newm.time1 + "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everyweek} (tag,text, time, weekday) VALUES ({tag}, {text}, {time}, {date})")
    async def job():
        await bot.send_message(message.from_user.id, newm.theme1)
    scheduler.add_job(job, 'cron', day_of_week=int(newm.date1),  hour=int(tl[0]), minute=int(tl[1]), id=newm.tag1, name=newm.name1)
    notiflist.append(newm.tag1 + ' - ' + newm.name1)
    await message.answer("Напоминание установлено.")
    print(newm.date1, ' ', newm.time1, ' ', newm.theme1, ' ', newm.tag1)
    print(notiflist)
    await state.finish()

@dp.message_handler(commands="remeveryweeksch", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.answer("Выберите какое напоминание хотите удалить и введите его тэг: \n")
    m = ''
    for i in notiflist:
        m += (i+'\n')
    await message.answer(m)
    print(notiflist)
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
            print(tag)
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everyweek} WHERE tag = {tag}")
    await message.reply("Напоминание успешно удалено.")
    print(notiflist)
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


@dp.message_handler(commands="nemm", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.answer(text='Отправьте день месяца и время, в которое будет отправляться данное напоминание: \n'
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
    nemm.name1 = message.text
    tl = nemm.time1.split(':')
    tag = "'" + nemm.tag1 + "'"
    text = "'" + nemm.theme1 + "'"
    date = "'" + nemm.date1 + "'"
    time = "'" + nemm.time1 + "'"
    async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
        async with aconn.cursor() as acur:
            await acur.execute(
                f"INSERT INTO {everymounth} (tag,text, time, mounthday) VALUES ({tag}, {text}, {time}, {date})")
    async def job():
        await bot.send_message(message.from_user.id, nemm.theme1)
    scheduler.add_job(job, 'cron', day=int(nemm.date1),  hour=int(tl[0]), minute=int(tl[1]), id=nemm.tag1, name=nemm.name1)
    notiflist.append(nemm.tag1 + ' - ' + nemm.name1)
    await message.answer("Напоминание установлено.")
    print(nemm.date1, ' ', nemm.time1, ' ', nemm.theme1, ' ', nemm.tag1)
    print(notiflist)
    await state.finish()

@dp.message_handler(commands="remeverymounthsch", state="*")
async def name_step(message: types.Message, state: FSMContext):
    await message.answer("Выберите какое напоминание хотите удалить и введите его тэг: \n")
    m = ''
    for i in notiflist:
        m += (i+'\n')
    await message.answer(m)
    print(notiflist)
    await delnots2.id.set()

@dp.message_handler(state=delnots2.id, content_types=types.ContentTypes.TEXT)
async def fname_step(message: types.Message, state: FSMContext):
    global everymounth
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
            print(tag)
            async with await psycopg.AsyncConnection.connect(DB_URI, sslmode="require") as aconn:
                async with aconn.cursor() as acur:
                    await acur.execute(
                        f"DELETE FROM {everymounth} WHERE tag = {tag}")
    await message.reply("Напоминание успешно удалено.")
    print(notiflist)
    await state.finish()

scheduler.start()

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
