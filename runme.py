import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import requests
import hashlib
from datetime import datetime, timedelta
import json
from collections import defaultdict
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ADMIN_IDS = [YOUR ADMIN ID]
USER_DATA_FILE = 'user_data.json'

BOT_TOKEN = 'YOUR BOT TOKEN'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

class CurrencyRates:
    def __init__(self, cbrf_url: str, crypto_api_url: str, crypto_api_key: str):
        self.cbrf_url = cbrf_url
        self.crypto_api_url = crypto_api_url
        self.crypto_api_key = crypto_api_key
        self.cbrf_cache = {}
        self.crypto_cache = {}
        self.last_update = datetime.now() - timedelta(hours=1)

    def get_fiat_rates(self):
        # Запрос курсов с CBRF
        logging.info("Запрос к CBRF API\n")
        response = requests.get(self.cbrf_url)
        data = response.json()
        self.cbrf_cache = {key: {'CharCode': value['CharCode'], 'Nominal': value['Nominal'], 'Value': value['Value']} for key, value in data['Valute'].items()}
        self.cbrf_cache['RUB'] = {'CharCode': 'RUB', 'Nominal': 1, 'Value': 1} # Костыль значений для RUB
        logging.info("CBRF курсы: %s", self.cbrf_cache)

    def get_crypto_rates(self):
        # Запрос курсов криптовалют
        url = f"{self.crypto_api_url}?fsyms=BTC,ETH,MATIC,SOL,USDT,BNB,TRX,TONCOIN,DOGE,LTC&tsyms=USD,EUR,RUB,BYN,UAH,CNY,JPY,GBP,KZT,UZS,BTC,ETH,MATIC,SOL,USDT,BNB,TRX,TONCOIN,DOGE,LTC"
        logging.info("Запрос к Crypto API\n")
        response = requests.get(url)
        self.crypto_cache = response.json()
        logging.info("Crypto курсы: %s", self.crypto_cache)

    def load_rates(self):
        logging.info("Запрос курсов валют...")
        self.get_fiat_rates()
        self.get_crypto_rates()
        self.last_update = datetime.now()
        logging.info("Курсы успешно загружены.")

    def get_rates(self):
        if (datetime.now() - self.last_update).total_seconds() > 3600:
            self.load_rates()
            logging.info("Курсы обновлены")
        return self.cbrf_cache, self.crypto_cache

class Userdata:
    def __init__(self):
        self.user_data = self.load_user_data()

    def load_user_data(self):
        try:
            with open(USER_DATA_FILE, 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return defaultdict(lambda: {"interactions": 0, "last_seen": None})

    def save_user_data(self, data):
        with open(USER_DATA_FILE, 'w') as file:
            json.dump(data, file, indent=4)

    def update_user_data(self, user_id):
        today = datetime.now().strftime('%Y-%m-%d')
        if user_id not in self.user_data:
            self.user_data[user_id] = {"interactions": 0, "last_seen": today}
        self.user_data[user_id]["interactions"] += 1
        self.user_data[user_id]["last_seen"] = today
        self.save_user_data(self.user_data)

userdata = Userdata()

currency_rates = CurrencyRates(
    'https://www.cbr-xml-daily.ru/daily_json.js', 
    'https://min-api.cryptocompare.com/data/pricemulti',
    'YOUR CRYPTOCOMPARE API KEY'
)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    userdata.update_user_data(message.from_user.id)
    newsurl = "https://t.me/CurbeeNews"
    # Создание кнопки
    keyboard = InlineKeyboardMarkup()
    howto = InlineKeyboardButton("❓ Помощь", callback_data='howto')
    news = InlineKeyboardButton("🗞 Новости", url=newsurl)
    feedback = InlineKeyboardButton("💭 Связь", callback_data='contact')
    keyboard.add(howto, news, feedback)
    
    # Отправка стартового сообщения с кнопкой
    await message.reply(
        '''<b>👋 Привет!</b>\n\nЯ Curbee — бот для получения актуальных курсов валют.\nИспользуйте inline-запросы для получения курсов валют и криптовалют.\n\n<i>Пример: @CurbeeBot 1 USD</i>''', 
        parse_mode="HTML",
        reply_markup=keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'howto')
async def process_howto_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "🐝 <b>Как работать с Curbee?</b>\n\nОтправьте inline-запрос с 2 или 3 аргументами\nвида: (количество) (исходная валюта) [валюта конвертации]\n\nК примеру:\n\n<pre>@CurbeeBot 1 USD</pre>Выведет все доступные конвертации из USD\n<pre>@CurbeeBot 1 ETH RUB</pre>Выведет курс для 1 ETH в рублях\n\nПриятного пользования!",
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data == 'news')
async def process_news_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        '''🗞 Новостной канал: @CurbeeNews\n\nВ этом канале будут новости по разработке и эксплуатации бота.\nНикакого спама, только важная информация!''',
        parse_mode="HTML"
    )

@dp.callback_query_handler(lambda c: c.data == 'contact')
async def process_contact_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        '''Связь с разработчиком: @CurbeeFBBot\n\nПишите, если испытываете какие-либо проблемы с ботом\nили хотите предложить добавление функционала!''',
        parse_mode="HTML"
    )

@dp.message_handler(commands=['stats'])
async def get_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("У вас нет прав для выполнения этой команды.")
        return
    
    today = datetime.now().strftime('%Y-%m-%d')
    total_users = len(userdata.user_data)
    interactions_today = sum(1 for user in userdata.user_data.values() if user['last_seen'] == today)
    new_users_today = sum(1 for user in userdata.user_data.values() if user['last_seen'] == today and user['interactions'] == 1)

    stats_message = (
        f"📊 Статистика бота:\n\n"
        f"👥 Общее количество пользователей: {total_users}\n"
        f"📅 Взаимодействий сегодня: {interactions_today}\n"
        f"🆕 Новых пользователей сегодня: {new_users_today}\n"
    )

    await message.reply(stats_message)

@dp.inline_handler()
async def inline_handler(query: InlineQuery):
    userdata.update_user_data(query.from_user.id)
    args = query.query.split()

    # Проверка на количество аргументов (2 или 3)
    if len(args) not in [2, 3]:
        return
    try:
        amount = float(args[0])
    except ValueError:
        return

    source_currency = args[1].upper()
    target_currency = args[2].upper() if len(args) == 3 else None

    fiat_symbols = "USD,EUR,RUB,BYN,UAH,CNY,JPY,GBP,KZT,UZS"
    crypto_symbols = "BTC,ETH,MATIC,SOL,USDT,BNB,TRX,TONCOIN,DOGE,LTC"

    # Словарь псевдонимов
    alias_map = {
        "TON": "TONCOIN"
    }

    # Применение псевдонимов
    source_currency = alias_map.get(source_currency, source_currency)
    if target_currency:
        target_currency = alias_map.get(target_currency, target_currency)

    # Получение кешированных значений
    cbrf_rates = currency_rates.get_rates()[0]
    crypto_rates = currency_rates.get_rates()[1]

    results = []

    # Обработка запросов с 2 аргументами (fiat и crypto)
    if len(args) == 2:
        # Фиатные валюты:
        if source_currency in cbrf_rates:
            base_rate = cbrf_rates[source_currency]['Value'] / cbrf_rates[source_currency]['Nominal']
            for fiat_currency in fiat_symbols.split(','):
                if fiat_currency == 'RUB':
                    converted_amount = amount * base_rate
                else:
                    rate = cbrf_rates[fiat_currency]['Value'] / cbrf_rates[fiat_currency]['Nominal']
                    converted_amount = amount * base_rate / rate
                title = f"{amount} {source_currency} = {converted_amount:.2f} {fiat_currency}"
                message_text = title
                results.append(
                    InlineQueryResultArticle(
                        id=hashlib.md5(title.encode()).hexdigest(),
                        title=title,
                        input_message_content=InputTextMessageContent(message_text=message_text)
                    )
                )

        # Криптовалюты:
        elif source_currency in crypto_symbols.split(','):
            for target_currency in fiat_symbols.split(','):
                if target_currency in crypto_rates[source_currency]:
                    rate = crypto_rates[source_currency][target_currency]
                    converted_amount = amount * rate
                    title = f"{amount} {source_currency} = {converted_amount:.2f} {target_currency}"
                    message_text = title
                    results.append(
                        InlineQueryResultArticle(
                            id=hashlib.md5(title.encode()).hexdigest(),
                            title=title,
                            input_message_content=InputTextMessageContent(message_text=message_text)
                        )
                    )

    # Обработка запросов с 3 аргументами (fiat to fiat, crypto to fiat, fiat to crypto, crypto to crypto)
    elif len(args) == 3:
        # Фиатная валюта в фиатную валюту
        if source_currency in fiat_symbols.split(',') and target_currency in fiat_symbols.split(','):
            source_rate = cbrf_rates[source_currency]['Value'] / cbrf_rates[source_currency]['Nominal']
            target_rate = cbrf_rates[target_currency]['Value'] / cbrf_rates[target_currency]['Nominal']
            converted_amount = amount * source_rate / target_rate
            title = f"{amount} {source_currency} = {converted_amount:.2f} {target_currency}"
            message_text = title
            results.append(
                InlineQueryResultArticle(
                    id=hashlib.md5(title.encode()).hexdigest(),
                    title=title,
                    input_message_content=InputTextMessageContent(message_text=message_text)
                )
            )
        # Криптовалюта в фиатную валюту
        elif source_currency in crypto_symbols.split(',') and target_currency in fiat_symbols.split(','):
            if target_currency in crypto_rates[source_currency]:
                rate = crypto_rates[source_currency][target_currency]
                converted_amount = amount * rate
                title = f"{amount} {source_currency} = {converted_amount:.2f} {target_currency}"
                message_text = title
                results.append(
                    InlineQueryResultArticle(
                        id=hashlib.md5(title.encode()).hexdigest(),
                        title=title,
                        input_message_content=InputTextMessageContent(message_text=message_text)
                    )
                )
        # Фиатная валюта в криптовалюту
        elif source_currency in fiat_symbols.split(',') and target_currency in crypto_symbols.split(','):
            if target_currency in crypto_rates and source_currency in crypto_rates[target_currency]:
                rate = 1 / crypto_rates[target_currency][source_currency]
                converted_amount = amount * rate
                title = f"{amount} {source_currency} = {converted_amount:.8f} {target_currency}"
                message_text = title
                results.append(
                    InlineQueryResultArticle(
                        id=hashlib.md5(title.encode()).hexdigest(),
                        title=title,
                        input_message_content=InputTextMessageContent(message_text=message_text)
                    )
                )
        # Криптовалюта в криптовалюту
        elif source_currency in crypto_symbols.split(',') and target_currency in crypto_symbols.split(','):
            if target_currency in crypto_rates[source_currency]:
                rate = crypto_rates[source_currency][target_currency]
                converted_amount = amount * rate
                title = f"{amount} {source_currency} = {converted_amount:.8f} {target_currency}"
                message_text = title
                results.append(
                    InlineQueryResultArticle(
                        id=hashlib.md5(title.encode()).hexdigest(),
                        title=title,
                        input_message_content=InputTextMessageContent(message_text=message_text)
                    )
                )
        else:
            title = f"К сожалению, у нас еще нет поддержки для {source_currency} или {target_currency}."
            message_text = title
            results.append(
                InlineQueryResultArticle(
                    id=hashlib.md5(title.encode()).hexdigest(),
                    title=title,
                    input_message_content=InputTextMessageContent(message_text=message_text)
                )
            )

    await query.answer(results, cache_time=1, is_personal=True)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)