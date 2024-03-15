from aiogram import Bot, Dispatcher,types, executor
from config import token
import sqlite3
import logging
from datetime import datetime 
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

connect = sqlite3.connect("bank.db",check_same_thread=False)
cursor = connect.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users(
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                lastname TEXT,
                phone_number VARCHAR (100)
        
);""")
cursor.execute(""" CREATE TABLE IF NOT EXISTS user_info(
               user_id INTEGER PRIMARY KEY,
               username  VARCHAR (150),
               first_name VARCHAR (150),
               last_name VARCHAR (150),
               balance INTEGER DEFAULT 0,
               data_regist DATETIME
);""")
connect.commit()

cursor.execute("""CREATE TABLE IF NOT EXISTS transfers (
            transfer_id INTEGER PRIMARY KEY,
            sender_id INTEGER,
            recipient_id INTEGER,
            amount REAL,
            FOREIGN KEY(sender_id) REFERENCES users(user_id),
            FOREIGN KEY(recipient_id) REFERENCES users(user_id)
);""")
connect.commit()


async def transfer_funds(sender_id, recipient_id, amount):
    cursor.execute("UPDATE user_info SET balance = balance - ? WHERE user_id = ?", (amount, sender_id))
    cursor.execute("UPDATE user_info SET balance = balance + ? WHERE user_id = ?", (amount,  recipient_id))
    cursor.execute("INSERT INTO transfers (sender_id, recipient_id, amount) VALUES (?, ?, ?)",
                   (sender_id, recipient_id, amount))
    connect.commit()

def get_balance(user_id):
    cursor.execute(f"SELECT balance FROM user_info WHERE user_id= {user_id} ")
    connect.commit()
    result = cursor.fetchone()
    return result[0] if result is not None else None

@dp.message_handler(commands='balance')
async def cmd_balance(message: types.Message):
    user_id = message.from_user.id
    balance = get_balance(user_id)
    if balance is not None:
     await message.answer(f"Ваш текущий баланс: {balance} сомов.")
    else:
        await message.answer("У вас пока нет счета. Для создания счета воспользуйтесь командой /start.")

class OrderPersonState(StatesGroup):
    lastname = State()
    username = State()
    phone_number = State()


buttons = [ 
    types.KeyboardButton("О нас"),
    types.KeyboardButton("Регистрация"),
    types.KeyboardButton('/balance'),
    types.KeyboardButton('/transfer'),
    types.KeyboardButton("/deposit")

]


key_buttons = types.ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)

@dp.message_handler(commands='start')
async def start(message: types.Message):

    cursor=connect.cursor()
    cursor.execute(f"SELECT user_id FROM user_info WHERE user_id = {message.from_user.id};")
    a = cursor.fetchall()
    if not a:
        cursor.execute(f"""INSERT INTO user_info (user_id, username, first_name, last_name,  data_regist) 
        VALUES ('{message.from_user.id}',  
               '{message.from_user.username}',
               '{message.from_user.first_name}',
               '{message.from_user.last_name}',
               '{datetime.now()}'
);""")
        connect.commit()

        await message.answer("""Здравствуйте , вас приветсвует компания 'Mbank'благодарим вас что выбрали именно нашу компанию.Пожалуйста чтобы в дальшем продолжить сотредничествa нажмите кнопку РЕГИСТРАЦИЯ  |
                          """, reply_markup = key_buttons)
        await message.answer(f"Ваш номер счет: {message.from_user.id}\nНикнейм: {message.from_user.username}")

@dp.message_handler(text = 'О нас')
async def about_us(message: types.Message):
    await message.answer("""Мы Mbank 🏦 являемся   одним из крупнейших копманий в КР. тБанк для всей страны ОАО «Коммерческий банк КЫРГЫЗСТАН» ведет свою историю с 01 января 1988 года в качестве Кирконторы Жилсоцбанка СССР, на основе которой 06 ноября 1990 года был создан Банк, зарегистрированный в МЮ КР как АКБ "Кыргызстан".
    В 2005 году Банк был преобразован в ОАО "АКБ Кыргызстан", а с 20 ноября 2006 года Банк носит нынешнее название ОАО «Коммерческий банк КЫРГЫЗСТАН», который ведет свою деятельность на основании лицензии на право осуществления банковских операций НБКР № 014.\n \nЧем занимается наша компания?👇🏻 \n-Мы заботимся о сбережениях каждого пользователя и несем полную отвественность за их безопастность.🔐 """,reply_markup=key_buttons)


class DepositState(StatesGroup):
    amount = State()


@dp.message_handler(commands='deposit') 
async def cmd_deposit(message: types.Message):
    await message.answer("Введите сумму для пополнения баланса:")
    await DepositState.amount.set()


@dp.message_handler(state=DepositState.amount)
async def deposit_amount(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cursor.execute('SELECT balance FROM user_info WHERE user_id = ?', (user_id,))
    balance = cursor.fetchone()[0]

    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")

        cursor.execute('UPDATE user_info SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        connect.commit()

        await message.answer(f"Баланс успешно пополнен на {amount} сом.")

    except ValueError as error:
        await message.answer(f"Ошибка: {error}")
        await state.finish()


@dp.message_handler(text='Регистрация')
async def registration(message: types.Message):
    await message.answer("Для регистрации нам нужны ваши данные:")
    await message.answer("Введите вашу фамилию:  ")
    await OrderPersonState.lastname.set()


@dp.message_handler(state = OrderPersonState.lastname)
async def first_n(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['lastname'] = message.text
    await message.answer("Введите ваше имя: ")
    await OrderPersonState.next()

@dp.message_handler(state = OrderPersonState.username)
async def later(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['username'] = message.text
    await message.answer("Введите ваш номер:")
    await OrderPersonState.next()

@dp.message_handler(state=OrderPersonState.phone_number)
async def num(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.text

        username = data['username']
        lastname = data['lastname']
        phone_number = data['phone_number']


        await message.answer("Вы теперь в базе, \n чтобы пополнить /deposit")
        await state.finish()

        cursor.execute(""" INSERT INTO users (username, lastname, phone_number)
                   VALUES (?,?,?) """, (username, lastname, phone_number ))
        connect.commit()


class TransferState(StatesGroup):
    amount = State()
    recipient_balance = State()

@dp.message_handler(commands=['transfer'])
async def transfer_command(message: types.Message):
    await message.answer('Введите сумму перевода:')
    await TransferState.amount.set()

@dp.message_handler(state=TransferState.amount)
async def process_amount(message: types.Message, state: FSMContext):
    amount = float(message.text)
    await state.update_data(amount=amount)
    await message.answer('Введите ID пользователя или номер счета получателя:')
    await TransferState.recipient_balance.set()

@dp.message_handler(state=TransferState.recipient_balance)
async def process_recipient_balance(message: types.Message, state: FSMContext):
    recipient_balance_data = int(message.text)
    data = await state.get_data()
    amount = data.get('amount')
    result = process_transfer(message.from_user.id, recipient_balance_data, amount)

    if result:
        await message.answer('Перевод выполнен успешно!')
        await message.answer(f'Сумма перевода: {amount} cом.')
        await message.answer(f'Получатель: {recipient_balance_data}')
        await message.answer(f"Осталось: {amount} сом.")
    else:
        await message.answer('Ошибка при выполнении перевода. Пожалуйста, проверьте данные получателя.')
 
        await state.finish()

def process_transfer(sender_id, recipient_balance_data, amount):
    connect = sqlite3.connect('bank.db')
    cursor = connect.cursor()     
    connect.execute('BEGIN TRANSACTION')

    cursor.execute('SELECT balance FROM user_info WHERE user_id = ?',
        (sender_id,))
    sender_balance = cursor.fetchone()[0]

    if sender_balance >=  amount:
            cursor.execute('UPDATE user_info SET balance = balance - ? WHERE user_id = ?', (amount, sender_id))

            cursor.execute('SELECT user_id FROM user_info WHERE user_id = ?', (recipient_balance_data,))
            recipient_exists = cursor.fetchone()

            if recipient_exists:
                cursor.execute('UPDATE user_info SET balance = balance + ? WHERE user_id = ?', (amount, recipient_balance_data))

                
                connect.execute('COMMIT')
                connect.commit()

@dp.message_handler()
async def a(message: types.Message):
    await message.answer("Я не понял ваш запрос, введите команду /start")


executor.start_polling(dp)

