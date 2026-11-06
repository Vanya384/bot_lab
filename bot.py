import asyncio  #для запуска асинхронного движка,для работы бота
import secret  
import logging  #обозначает работу бота
from datetime import datetime  #текущая дата и время на компьютере
import random  #для выбора рандомных чисел
import aiohttp  #отвечает за работу со сторонними API
from aiogram import Bot, Dispatcher, F  #Bot-отвечает за отправку сообщений, кнопок и т.д. пользователю;
                                         #Dispatcher принимает все сообщения от пользователей и на их основе принимает соответствующие решения;
                                          #F- фильтр.Он сверяет данные введенные пользователем и сверяет их с ожидаемыми;
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton  #Message -контейнер,представляет собой входящее либо выходящее сообщение;
                                                                         #ReplyKeyboardMarkup-отвечает за создание кнопок;
                                                                          #KeyboardButton-при нажатии на кнопку будет отправляться сообщение на кнопке
from aiogram.filters import CommandStart   #фильтр,реагирующий именно на команду /start

Token = secret.token_secret
bot = Bot(token=Token)  #управление ботов через мой аккаунт в телеграм
dp = Dispatcher()  #мозг программы
log_file = "bot_log.txt"  #файл,куда будут записываться все действия пользователей

try:
    with open(log_file, 'x', encoding='utf-8') as f:  #x-используем вместо w,т.к. он проверяет наличие этого файла(т.е. если он есть,то новый создаваться не будет)
        f.write("Unical_ID\t @telegram_nickname\t Motion\t API\t Date\t Time\t API_answer\n")  #Motin-действи,совершенное пользователем,
                                                                                                #API-сервис,к которому был отправлен запрос
                                                                                                 #ответ от сервера(ошибка,успешно и т.д.)
except FileExistsError:  #если файл уже существует,то питон отлавливает ошибку ,которая возникнет при проверке 'x'(если не будет отлова,то программа ляжет на этой ошибке)
    pass  #далее мы ничего не делаем

def log_action(user_id: int, nickname: str, motion: str, API_name: str, API_answer: str):
    now = datetime.now()   #фиксируем момент времени
    date_str = now.strftime("%Y-%m-%d")  #видоизменяем дату в строку необходимого формата
    time_str = now.strftime("%H:%M:%S")  #видоизменяем время

    if nickname:
        tg_nick = f"@{nickname}"
    else:
        tg_nick = "No_nickname"
              
    log_line = f"{user_id}\t{tg_nick}\t{motion}\t{API_name}\t{date_str}\t{time_str}\t{API_answer}\n"
    
    with open(log_file, 'a', encoding='utf-8') as f:  #дозаписываем в log_file полученные данные
        f.write(log_line)


keyboard = ReplyKeyboardMarkup(keyboard = [ [KeyboardButton( text = "Курс валют (НБРБ)"), KeyboardButton( text = "Книги")] , [KeyboardButton( text = "Цитаты")] ], resize_keyboard = True) #создание кнопок
                                                                                                                                                                                                         #resize_keyboard -автоматически настраивает размер кнопок под устройство пользователя


@dp.message(CommandStart())  #CommandStart() срабатывает только в случае "/start"
async def cmd_start(message: Message):  #функция асинхронная для того,чтобы бот мог обслуживать сразу несколько пользователей
                                         #Message-информация о пользователе
    log_action(message.from_user.id, message.from_user.username, "command /start", "none", "none") #в конце два none, т.к. пользователь еще не обращался к сервисам
    await message.answer(f"Привет, {message.from_user.first_name}! Бот готов к работе.\n Выбери нужный раздел на кнопках ниже:", reply_markup = keyboard)  #reply_markup обозначает ,что будет происходить видоизменение чата
                                                                                                                                                      #т.е. появятся кнопки

@dp.message(F.text == "Курс валют (НБРБ)")
async def get_by_currency(message: Message):
    API_url = "https://api.nbrb.by/exrates/rates?periodicity=0"  #ссылка на структурированный текст курсов валют НацБанка Республики Беларусь
    async with aiohttp.ClientSession() as session:  #открытие браузера для отправки запросов

        try:
            async with session.get(API_url) as response:  #переход по ссылке и ожидание ответа банка

                if response.status == 200:  #если статус 200 == все отлично
                    data = await response.json()  #полученные данные в виде текста превращаются в список для удобства
                    target_currencies = ['USD', 'EUR', 'RUB', 'CNY']  #выбираем те валюьты,курсы по отношению к которым нами востребованы
                    rates = {}  #блок для записи необходимых валют
                    
                    for item in data:
                        abbr = item.get("Cur_Abbreviation")

                        if abbr in target_currencies:   #если валюта совпала с необходимой,то берем то,что нам нужно
                            name = item.get("Cur_Name")           # Имя валюты
                            scale = item.get("Cur_Scale")         # Кратность (например: 100 для RUB)
                            rate = item.get("Cur_OfficialRate")   # Курс в BYN
                            rates[abbr] = (name, scale, rate)      #записываем в наш блок элемент в виде массива данных
                    
                    answer_text = "Официальный курс валют НБРБ:\n"

                    for abbr in target_currencies:

                        if abbr in rates:  #если валюта находится в списке необходимых,то выписываем ранее записыанные данные из rates(берем элемент abbr из массива rates)
                            name, scale, rate = rates[abbr] #присваиваем переменные name, scale, rate значения в элементе abbr
                            answer_text += f"{scale} {abbr} {name} = {rate} BYN\n"  #выводим текстом
                    
                    log_action(message.from_user.id, message.from_user.username, "Button click", "NBRB API", "success")  #вызываем ф-цию log_action() и передаем туда 5 значений
                    await message.answer(answer_text)  #выводим сообщение пользователю в тот же чат

                else:
                    log_action(message.from_user.id, message.from_user.username, "Button click", "NBRB API", "error")  #в противном случае выводим ошибку
                    await message.answer("Нацбанк не ответил на запрос")

        except Exception:
            log_action(message.from_user.id, message.from_user.username, "Button click", "NBRB API", "failed") #если банк изначально не ответил,то чтобы бот не ложился для всех пользователей,он предупредит пользователя
            await message.answer("Не удалось установить соединение с сервером НБРБ\n")


@dp.message(F.text == "Цитаты")
async def get_proverb_info(message: Message):
    API_url = "https://dummyjson.com/quotes?limit=3"   #запрашиваем 3 цитаты
    
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"User-Agent": "TelegramBot/1.0"}
            async with session.get(API_url, headers=headers) as response:

                if response.status == 200:
                    json_data = await response.json() 
                    quotes_list = json_data.get("quotes", [])
                    if not quotes_list:   #если нет пословиц
                        await message.answer("К сожалению, цитаты не найдены.")
                        return

                    result_text = ""
                    for i, item in enumerate(quotes_list, 1):
                        quote_text = item.get("quote", "").strip()
                        author = item.get("author", "").strip()
                        if not author:
                            author = "Народная мудрость"
                        result_text += f"{i}. «{quote_text}» — {author}\n"
                    
                    await message.answer(f"Вот 3 цитаты для вас:\n{result_text}")
                    log_action(message.from_user.id, message.from_user.username, "Button click", "DummyJSON API", "success")
                
                else:
                    log_action(message.from_user.id, message.from_user.username, "Button click", "DummyJSON API", "error")
                    await message.answer("Не удалось найти цитату (ошибка сервера)")
        
        except Exception:
            log_action(message.from_user.id, message.from_user.username, "Button click", "DummyJSON API", "failed")
            await message.answer("Не удалось установить соединение с сервером цитат.")


@dp.message(F.text == "Книги")
async def ask_for_book_title(message: Message):
    log_action(message.from_user.id, message.from_user.username, "Button click", "none", "waiting_for_input")
    await message.answer("Введите название книги для поиска:")

@dp.message(F.text) 
async def handle_book_search_or_unknown(message: Message):
    user_text = message.text
    log_action(message.from_user.id, message.from_user.username, "Text input (Book Search)", "OpenLibrary API", "processing")
    API_url = f"https://openlibrary.org/search.json?q={user_text}&limit=1&language=rus"

    async with aiohttp.ClientSession() as session:
        try:
            headers = {"User-Agent": "TelegramBot/1.0"}
            async with session.get(API_url, headers=headers) as response:

                if response.status == 200:
                    json_data = await response.json()
                    docs = json_data.get("docs", []) 

                    if not docs:
                        log_action(message.from_user.id, message.from_user.username, "Search result", "OpenLibrary API", "not_found")
                        await message.answer(f"По запросу «{user_text}» ничего не найдено.\n Попробуйте изменить название.")
                        return
                    
                    book = docs[0]
                    title = book.get("title", "Название неизвестно")
                    authors_list = book.get("author_name", [])

                    if authors_list:
                        author = ", ".join(authors_list)  

                    else:
                        author = "Автор неизвестен"

                    year = book.get("first_publish_year", "")
                    subjects = book.get("subject", [])
                    if subjects:
                        topics = ", ".join(subjects[:3])

                    else:
                        topics = "Темы не указаны"

                    answer = (f"Найдена книга:\n" f"Название: {title}\n" f"Автор: {author}\n" f"Год издания: {year}\n" f"Темы: {topics}")
                    
                    log_action(message.from_user.id, message.from_user.username, "Search result", "OpenLibrary API", "success")
                    await message.answer(answer)
                    
                else:
                    log_action(message.from_user.id, message.from_user.username, "Search error", "OpenLibrary API", "error")
                    await message.answer("Ошибка при обращении к базе книг.")

        except Exception:
            log_action(message.from_user.id, message.from_user.username, "Search failed", "OpenLibrary API", "failed")
            await message.answer("Не удалось подключиться к сервису поиска книг.")


async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот успешно запущен и ведет лог в файл bot_log.txt...\n")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())   #для асинхронной работы
