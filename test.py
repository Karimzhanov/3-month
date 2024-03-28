from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import random
import string
import sqlite3

TOKEN = '6747046477:AAGSlivEtSSMd220tsxFwYfKQFCK0D9RnyQ'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

conn = sqlite3.connect('clients.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS clients
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  first_name TEXT,
                  last_name TEXT,
                  phone_number TEXT,
                  personal_code TEXT,
                  warehouse_address TEXT)''')
conn.commit()

def generate_personal_code():
    code = ''.join(random.choices(string.ascii_uppercase, k=3)) + '-' + ''.join(random.choices(string.digits, k=3))
    return code

class RegisterProcess(StatesGroup):
    last_name = State()
    phone_number = State()
    warehouse_address = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Для регистрации введите /register.")

@dp.message_handler(commands=['register'])
async def register(message: types.Message):
    await message.reply("Для регистрации, пожалуйста, введите своё имя.")

@dp.message_handler(state=None) 
async def process_name(message: types.Message):
    await RegisterProcess.last_name.set() 
    await message.reply("Спасибо! Теперь введите свою фамилию.")

@dp.message_handler(state=RegisterProcess.last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['first_name'] = message.text
    await RegisterProcess.next()  
    await message.reply("Отлично! Теперь введите свой номер телефона.")

@dp.message_handler(state=RegisterProcess.phone_number)
async def process_phone_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['last_name'] = message.text
    await RegisterProcess.next()  
    await message.reply("Прекрасно! Теперь введите адрес вашего склада в Китае.")

@dp.message_handler(state=RegisterProcess.warehouse_address)
async def process_warehouse_address(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone_number'] = message.text
        data['warehouse_address'] = message.text
        data['personal_code'] = generate_personal_code()
    cursor.execute('''INSERT INTO clients (first_name, last_name, phone_number, personal_code, warehouse_address) 
                      VALUES (?, ?, ?, ?, ?)''',
                   (data['first_name'], data['last_name'], data['phone_number'], data['personal_code'], data['warehouse_address']))
    conn.commit()
    await message.reply(f"Ваш персональный код: {data['personal_code']}. Регистрация завершена.")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
