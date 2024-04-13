import asyncio
import sqlite3
import requests
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import time

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '7121734281:AAFfppq_MIImVmB56Lmc2x9OKXnoSqqEv5w'
bot = Bot(TOKEN)
dp = Dispatcher(bot)


DB_FILE = 'subscribers.db'

def create_table():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS subscribers (
                        id INTEGER PRIMARY KEY,
                        chat_id INTEGER UNIQUE NOT NULL,
                        status TEXT NOT NULL,
                        last_payment_date TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS receipt (
                        id INTEGER PRIMARY KEY,
                        payment_code INTEGER UNIQUE NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        direction TEXT,
                        amount TEXT,
                        date TEXT
                    )''')
    conn.commit()
    conn.close()

create_table()

async def start(message: types.Message):
    chat_id = message.chat.id
    if not is_subscriber(chat_id):
        add_subscriber(chat_id)
        payment_button = InlineKeyboardButton("Оплатить", callback_data="payment")
        keyboard = InlineKeyboardMarkup().add(payment_button)
        await bot.send_message(chat_id=chat_id, text="Привет! Для вступления в группу оплатите 100 сом.", reply_markup=keyboard)
    else:
        await bot.send_message(chat_id=chat_id, text="Привет! Ты уже в группе.")

async def help_command(message: types.Message):
    await message.reply_text("Это помощь. Здесь должны быть правила группы.", reply_markup=get_help_keyboard())

async def handle_text(message: types.Message):
    pass

async def handle_material_link(message: types.Message):
    chat_id = message.chat.id
    material_link = message.text
    
    response = requests.get(material_link)
    if response.status_code == 200:
        await bot.send_document(chat_id=chat_id, document=response.content)
    else:
        await bot.send_message(chat_id=chat_id, text="Не удалось загрузить материал.")

def add_subscriber(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO subscribers (chat_id, status) VALUES (?, ?)", (chat_id, "pending_payment"))
    conn.commit()
    conn.close()

def is_subscriber(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subscribers WHERE chat_id=?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def remove_subscriber(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscribers WHERE chat_id=?", (chat_id,))
    conn.commit()
    conn.close()

def check_monthly_payment():
    today = datetime.now()
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers WHERE status='active' AND last_payment_date < ?", (first_day_of_month,))
    overdue_subscribers = cursor.fetchall()
    
    for chat_id in overdue_subscribers:
        remove_subscriber(chat_id[0])

async def buy(message: types.Message):
    try:
        chat_id = message.chat.id
        button = InlineKeyboardButton("Оплатить", callback_data="payment")
        keyboard = InlineKeyboardMarkup([[button]])
        await bot.send_message(chat_id=chat_id, text="Нажмите на кнопку, чтобы оплатить", reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Ошибка в обработке команды /buy: {e}")

async def handle_button(query: types.CallbackQuery):
    chat_id = query.message.chat.id
    data = query.data
    if data == 'payment':
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton("Mbank", callback_data="mbank_payment"),
                    InlineKeyboardButton("Megapay", callback_data="megapay_payment")
                ]
            ]
        )
        await bot.send_message(chat_id=chat_id, text="Выберите способ оплаты:", reply_markup=reply_markup)
    elif data == 'mbank_payment':
        await process_payment(chat_id, 'mbank', query)
    elif data == 'megapay_payment':
        await process_payment(chat_id, 'megapay', query)
    elif data == 'help':
        await help_command(query.message)

async def process_payment(chat_id, payment_method, query):
    try:
        # Ваш код для обработки платежа здесь
        # Например, вызываем API вашей платежной системы для запроса чека оплаты
        payment_id = query.id  # ID платежа, который мы будем использовать при запросе чека оплаты
        api_url = "https://example.com/payment/check"  # Пример URL для запроса чека оплаты
        payload = {
            "payment_id": payment_id,
            "payment_method": payment_method
        }
        headers = {
            "Authorization": "Bearer YOUR_API_TOKEN",
            "Content-Type": "application/json"
        }
        response = requests.post(api_url, json=payload, headers=headers)
        
        # Проверяем успешность запроса чека оплаты
        if response.status_code == 200:
            receipt = response.json()  # Получаем чек оплаты из ответа
            # Проверяем успешность платежа в чеке оплаты
            if receipt.get('status') == 'success':
                await bot.send_message(chat_id=chat_id, text=f"Платеж успешно обработан. Спасибо за оплату!")
                
                # Добавляем данные в базу данных
                direction = "dfghjk"
                amount = "dfghjk"
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO receipt (payment_code, first_name, last_name, direction, amount, date) VALUES (?, ?, ?, ?, ?, ?);",
                               (payment_id, "0999838684", "dfghjk", direction, amount, time.ctime()))
                conn.commit()
                conn.close()
            else:
                await bot.send_message(chat_id=chat_id, text="Ошибка при обработке платежа. Пожалуйста, попробуйте еще раз или обратитесь в службу поддержки.")
        else:
            await bot.send_message(chat_id=chat_id, text="Ошибка при запросе чека оплаты.")
    except Exception as e:
        await bot.send_message(chat_id=chat_id, text="Произошла ошибка при обработке платежа. Пожалуйста, попробуйте еще раз или обратитесь в службу поддержки.")

async def send_subscription_reminder():
    today = datetime.now()
    end_of_month = today.replace(day=1, month=today.month+1, hour=0, minute=0, second=0) - timedelta(days=3)
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM subscribers WHERE status='active'")
    active_subscribers = cursor.fetchall()
    conn.close()
    
    for chat_id in active_subscribers:
        await bot.send_message(chat_id=chat_id[0], text="Напоминаем вам, что до конца месяца осталось 3 дня. Пожалуйста, оплатите подписку.")

def get_start_keyboard():
    button = InlineKeyboardButton("Помощь", callback_data="help")
    return InlineKeyboardMarkup().add(button)

def get_help_keyboard():
    button = InlineKeyboardButton("Оплатить", callback_data="payment")
    return InlineKeyboardMarkup().add(button)

async def main():
    # Регистрируем обработчики
    dp.register_message_handler(start, commands="start")
    dp.register_message_handler(help_command, commands="help")
    dp.register_message_handler(buy, commands="buy")  # Добавляем обработчик для команды /buy
    dp.register_message_handler(handle_text, content_types=types.ContentType.TEXT)
    dp.register_message_handler(handle_material_link, content_types=types.ContentType.TEXT, regexp=r'https?://\S+')
    dp.register_callback_query_handler(handle_button, lambda query: query.data in ['payment', 'mbank_payment', 'megapay_payment', 'help'])
    
    # Получаем список зарегистрированных обработчиков
    registered_handlers = dp.message_handlers
    print("Registered handlers:", registered_handlers)
    
    # Проверяем ежемесячные оплаты
    check_monthly_payment()

    # Отправляем напоминание о подписке
    await send_subscription_reminder()

    # Запускаем бота
    await dp.start_polling()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    