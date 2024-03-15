import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, types, executor
from config import token  

# Инициализация бота и диспетчера
bot = Bot(token=token)
dp = Dispatcher(bot)

# Функция для обработки команды /start
async def start(message: types.Message):
    await message.answer("Привет! Я бот новостей. Чтобы получить новости, введите команду /news.")

# Функция для обработки команды /news
async def news(message: types.Message):
    # Проходим по страницам с новостями
    for page in range(1, 11):
        url = f'https://24.kg/page_{page}'
        try:
            # Запрос к веб-сайту
            response = requests.get(url=url)
            response.raise_for_status()  # Проверка успешности запроса
            # Парсинг HTML с помощью BeautifulSoup
            soup = BeautifulSoup(response.text, 'lxml')
            # Поиск всех новостей на странице
            all_news = soup.find_all('div', class_='title')
            # Отправка каждой новости пользователю
            for news in all_news:
                # Разбиваем текст новости на части длиной не более 4096 символов
                news_text = news.text
                while len(news_text) > 0:
                    await message.answer(news_text[:4096])
                    news_text = news_text[4096:]
        except Exception as e:
            # Обработка ошибок и отправка сообщения об ошибке
            await message.answer(f"Произошла ошибка при получении новостей: {e}")

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    await start(message)

# Обработчик команды /news
@dp.message_handler(commands=['news'])
async def handle_news(message: types.Message):
    await news(message)

# Запуск бота
executor.start_polling(dp)
