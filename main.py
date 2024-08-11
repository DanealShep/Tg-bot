import PRICE
import payments as payments
import texts
from aiogram.dispatcher.filters import IDFilter
from telebot.apihelper import unban_chat_member
from threading import Thread
import config  # добавить файл config
import logging  # добавить модуль logging
import time
from aiogram.utils import executor
import sqlite3
from aiogram import *
from aiogram.types import *
from aiogram.types import message
import datetime
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
import currency_converter
from currency_converter import CurrencyConverter

# aipgram , список . (aiogram.types) - серая папка
# (aiogram.types.user) - фаул пайтон. Можно пропускать название списка
# aiogram.types.callback_query

# log
logging.basicConfig(level=logging.INFO)

# init
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)
wm = texts.welcometext
ht = texts.helptext
ut = texts.User_agreement
st = texts.status


# бан для новых пользователей
# пользователь входит в чат (его нет в базе данных)
# хендлер принимает пользователя, который зашёл
# сканирует всех
# те, кто зашёл - вытаскиваем их id и сверяем с базой данных


# разбан забаненных вошедших - РАБОТАЕТ!!!))) Вызывается после оплаты
async def unban():
    connect = sqlite3.connect("Datas.db")
    cursor = connect.cursor()
    dn = datetime.now()
    cursor.execute(f"SELECT ban_id FROM ban_users")
    ban_db = cursor.fetchall()
    print(ban_db)
    for a in ban_db:
        print(a)
        for b in a:
            print(b)
            cursor.execute(
                f"SELECT tg_users_id, Subs_status, DATE_of_end_subs FROM users WHERE tg_users_id = {b}")  # если забаненный пользователь
            main_db = cursor.fetchone()
            print(main_db)
            if main_db is not None:
                print(" main_db yes")
                if main_db[1] is not None:
                    print("main_db[1] is not None")
                    if main_db[1] == bool(0):
                        print("забаненный пользователь вошёл в бота")
                    elif main_db[1] == bool(1):
                        if main_db[2] is not None:
                            if datetime.strptime(main_db[2], '%Y-%m-%d %H:%M:%S.%f') >= dn:
                                print("з.п приобрёл подписку и будет разбанен")
                                await bot.unban_chat_member(chat_id=config.GROUP_ID, user_id=main_db[0],
                                                            only_if_banned=True)
    connect.close()


# БАН ВОШЕДШИХ ПОЛЬЗОВАТЕЛЕЙ  - РАБОТАЕТ!!!))   Хендлер есть!
@dp.message_handler(content_types="new_chat_members")
async def join_chat_members(message: types.Message):
    connect = sqlite3.connect("Datas.db")
    cursor = connect.cursor()
    ucd = message.new_chat_members[0].id  # user_chat_id = ucd
    print(ucd)
    cursor.execute(f"SELECT tg_users_id, Subs_status, DATE_of_end_subs FROM users WHERE tg_users_id = {ucd}")
    stroka = cursor.fetchone()
    dn = datetime.now()  # dn datetime now
    if stroka is None:  # Если его нет в базе данных(значит кто-то скинул ему ссылку)
        await bot.ban_chat_member(chat_id=config.GROUP_ID, user_id=ucd)
        cursor.execute("""INSERT INTO ban_users(ban_id) VALUES (?)""", (f"{ucd}",))
        print("пользователя нет. Он будет забанен")
    elif stroka[0] == ucd and (datetime.strptime(stroka[2], '%Y-%m-%d %H:%M:%S.%f') <= dn or stroka[
        2] is None):  # Если он есть в базе данных, но нет подписки или она просрочена(просто зашёл в бота и перешёл по ссылке)
        await bot.ban_chat_member(chat_id=config.GROUP_ID, user_id=ucd)
        cursor.execute("""INSERT INTO ban_users(ban_id) VALUES (?)""", (f"{ucd}",))
        print("пользователь есть в базе данных. У него нет подписки или она просрочена")

    connect.commit()
    connect.close()


# блокировка по истечению подписки для тех, кто оплачивал подписку и её срок истёк.

async def ban_for_users():  # Работает! Хендлер каждые 10 секунд
    connect = sqlite3.connect("Datas.db")
    cursor = connect.cursor()
    cursor.execute(f"SELECT tg_users_id, Subs_status, DATE_of_end_subs FROM users WHERE Subs_status = {bool(1)}")
    old_db = cursor.fetchall()  # Все строки с подпиской
    dm = datetime.now()
    print(old_db)  # [(0,1,2), и т.д
    for c in old_db:
        print(c)  # В строке мы перебираем с, где с - это одна любая строка
        print(c[2])  # последнее значение в строке то есть дата в формате стр
        print(c[0])
        if datetime.strptime(c[2], '%Y-%m-%d %H:%M:%S.%f') <= dm:  # если подписка просрочена
            print("у пользователя кончилась подписка0")

            # cursor.execute(f"""UPDATE users SET Subs_status = {bool(0)} WHERE tg_users_id = {c[0]} AND DATE_of_end_subs = '{datetime.strptime(c[2], '%Y-%m-%d %H:%M:%S.%f')}' """) #Дата конца подписки (стр) = стр дата
            print("у пользователя кончилась подписка")
            await bot.ban_chat_member(chat_id=config.GROUP_ID, user_id=c[0])
            cursor.execute("""INSERT OR IGNORE INTO ban_users(ban_id) VALUES (?)""", (f"{c[0]}",))

    connect.commit()
    connect.close()


async def infinite_loop():
    while True:
        # Здесь можно добавить любую логику, которую нужно выполнять каждую секунду
        print('Запускаю асинхронную задачу...')
        await unban_for_users()
        await asyncio.sleep(3)
        await ban_for_users()
        await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.create_task(infinite_loop())


async def money_loop():  # Денежный приход раз в месяц:  # Работает!!!)   # Для нас осталось сделать обновление данных
    while True:
        plus = timedelta(seconds=10)
        dn = datetime.now()

        a = datetime.strptime("2024-07-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        b = datetime.strptime("2024-06-27 00:14:00", '%Y-%m-%d %H:%M:%S')
        c = datetime.strptime("2024-09-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        d = datetime.strptime("2024-10-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        e = datetime.strptime("2024-11-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        f = datetime.strptime("2024-12-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        g = datetime.strptime("2025-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        h = datetime.strptime("2025-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        i = datetime.strptime("2025-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        j = datetime.strptime("2025-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        k = datetime.strptime("2025-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        n = datetime.strptime("2025-01-01 00:00:00", '%Y-%m-%d %H:%M:%S')
        tuples = [(a,), (b,), (c,), (d,), (e,), (f,), (g,), (h,), (i,), (j,), (k,), (n,)]
        for t in tuples:
            for t1 in t:
                if t1 <= dn <= (t1 + plus):  # Больше или равно и меньше или равно.
                    print(t1 <= dn <= (t1 + plus))
                    await money_count()
                    print("ДАТА")
                    await asyncio.sleep(2160000)
                else:
                    await asyncio.sleep(1)


loop = asyncio.get_event_loop()
loop.create_task(money_loop())


# Условия разбана для старых, у кого подписка истекла, ушли в бан, но решили продлить.
async def unban_for_users():  # РАБОТАЕТ!!!))) вызывается также этим функций
    connect = sqlite3.connect("Datas.db")
    cursor = connect.cursor()

    cursor.execute(
        f"SELECT tg_users_id, Subs_status, DATE_of_end_subs FROM users WHERE Subs_status = {bool(1)}")  # подписка уже была приобретена
    old1_db = cursor.fetchall()
    dl = datetime.now()
    for e in old1_db:
        if datetime.strptime(e[2], '%Y-%m-%d %H:%M:%S.%f') >= dl:
            print("Пользователь в чате продлил подписку - разбанить")
            print(e[0])
            await bot.unban_chat_member(chat_id=config.GROUP_ID, user_id=e[0], only_if_banned=True)
    connect.close()


async def money_count():  # Запускать раз в месяц
    connect = sqlite3.connect("Datas.db")
    cursor = connect.cursor()

    cursor.execute(f"SELECT money_rub FROM users WHERE money_rub IS NOT NULL ")
    cRUB = cursor.fetchall()
    cursor.execute(f"SELECT money_eur FROM users WHERE money_eur IS NOT NULL ")
    cEUR = cursor.fetchall()
    if cRUB or cEUR is not None:
        i = list(map(sum, cRUB))
        print(i)
        summar = sum(i)
        print(summar)  # Считает общую сумму рублей поступившую за всё время summar = k+b (внешний параметр)

        e = list(map(sum, cEUR))
        summae = sum(e)  # Считает общую сумму евро поступившую за всё время summae
        print(summae)
        cursor.execute(f"SELECT RUB FROM money")  # a - пред.   здесь мы считаем общее
        RUBS = cursor.fetchall()
        print(RUBS)
        sumps = list(map(sum, RUBS))
        summarps = sum(sumps)  # сумма всех до рубли

        cursor.execute(f"SELECT EUR FROM money")
        EURS = cursor.fetchall()
        print(EURS)
        sumeur = sum(list(map(sum, EURS)))  # cумма всех до евро
        print(summarps)
        print(sumeur)

        a = (summar - summarps)  # Прибыль в рублях
        print(a)
        b = (summae - sumeur)  # Прибыль в евро
        print(b)
        DATE = datetime.now()

        cursor.execute("""INSERT INTO money(RUB, EUR, DATE) VALUES (?, ? ,?)""", (f"{a}", f"{b}", f"{DATE}"))

    connect.commit()
    connect.close()


# Меню
@dp.message_handler(commands=['start'])
async def cmd_handler(message: types.Message):
    if not message.chat.type == 'private':

        pass
        await message.bot.delete_message(chat_id=config.GROUP_ID,
                                         message_id=message.message_id)  # удаление сообщений бота из группового чата

    else:

        await message.answer(
            "Приветствуем тебя, {0.first_name} !👋".format(message.from_user, bot.get_me()),
            parse_mode='html')
        time.sleep(2.0)

        # base data
        connect = sqlite3.connect("Datas.db")
        cursor = connect.cursor()

        user_id = message.from_user.id
        user_name = message.from_user.username
        user_firstname = message.from_user.first_name

        cursor.execute(f"SELECT tg_users_id FROM users WHERE tg_users_id={user_id}")
        data = cursor.fetchone()
        if data is None:
            user_id = message.from_user.id
            user_name = message.from_user.username
            user_firstname = message.from_user.first_name

            cursor.execute("""INSERT INTO users 
            (tg_users_id, users_name, users_firstname)
            VALUES (?, ?, ?)""", (f"{user_id}", "@" + f"{user_name}",
                                  f"{user_firstname}"))  # ? - плейсхолдеры. Просто занимают место, а в них летят функции f' #столбцы таблицы

        else:
            user_id = message.from_user.id
            user_name = message.from_user.username
            user_firstname = message.from_user.first_name
            cursor.execute(f"""UPDATE users SET users_name = '{"@" + user_name}', users_firstname = '{user_firstname}'
            WHERE tg_users_id = '{user_id}' AND (users_name <> '{"@" + user_name}' 
            OR users_firstname <> '{user_firstname}') """)

        connect.commit()
        connect.close()

        markup = types.InlineKeyboardMarkup(row_width=1)
        item = types.InlineKeyboardButton('Тех.поддержка 🙋', callback_data='help')
        item2 = types.InlineKeyboardButton("Оплата 💳", callback_data='buymenu')
        item3 = types.InlineKeyboardButton("Условия подписки 📑", callback_data="subscription info")
        itemm = types.InlineKeyboardButton("Статус подписки", callback_data='status')
        markup.add(item2, item3, item, itemm)
        await message.answer(wm, reply_markup=markup)  # wm Приветственный текст


@dp.callback_query_handler(lambda call: True)
async def answe(call: CallbackQuery):
    # Тех.поддержка
    if call.data == 'help':
        markupmenuT = types.InlineKeyboardMarkup(resize_keyboard=True)
        FAQT = types.KeyboardButton("FAQ ❓", callback_data="FAQ")
        helpT = types.KeyboardButton("Поддержка 🎧", callback_data="writeadmin")
        bkT = types.KeyboardButton('⬅', callback_data='backt1')
        markupmenuT.add(FAQT, helpT, bkT)
        await call.message.answer(ht, reply_markup=markupmenuT)
    elif call.data == 'backt1':
        await call.message.delete()

    if call.data == 'writeadmin':
        await call.message.answer("https://t.me/helpmetaleader - Напиши свой вопрос в чате, и мы обязательно ответим")
        # Условия подписки
    if call.data == 'subscription info':
        markupmenuS = types.InlineKeyboardMarkup(resize_keyboard=True)
        bks = types.KeyboardButton('⬅', callback_data='backt1')
        markupmenuS.add(bks)
        await call.message.answer(
            ut,
            reply_markup=markupmenuS)
    elif call.data == 'backt1':
        await call.message.delete()

        # Статус подписки 0 РАБОТАЕТ!!!)
    if call.data == 'status':
        markupmenuC = types.InlineKeyboardMarkup(resize_keyboard=True)
        bkC = types.KeyboardButton('⬅', callback_data='backC')
        markupmenuC.add(bkC)

        connect = sqlite3.connect("Datas.db")
        cursor = connect.cursor()

        cursor.execute("SELECT * FROM users")
        for person in cursor.fetchall():
            print(f"{person[0]} - {person[1]}")

        connect.commit()
        connect.close()

        connect = sqlite3.connect("Datas.db")
        cursor = connect.cursor()
        daten = datetime.now()
        id = call.from_user.id
        print(id)
        cursor.execute(f"SELECT * FROM users WHERE tg_users_id = {id} ")
        alldb = cursor.fetchall()
        for h in alldb:  # (кто просто зашёл в бота) одна строка
            if h[5] is not None:  # Приобретал подписку
                if datetime.strptime(h[5], '%Y-%m-%d %H:%M:%S.%f') >= daten:  # Подписка активирована
                    print("Статус = Приобретенна подписка активирована")
                    print("Дата окончания подписки = datetime")
                    if h[3] is not None:
                        if h[3] == 100:

                            await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                                     bot.get_me()) + '. Ваша подписка  \n Статус: активирована ✅\n \n' \
                                                                                                     " Ваш тариф 🧾: (1 месяц, 100 RUB) \n Время оплаты📅:" +
                                                      h[4] + "\n Время окончания⏳:" + h[5], parse_mode='html',
                                                      reply_markup=markupmenuC)
                        elif h[3] == 300:

                            await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                                     bot.get_me()) + '. Ваша подписка  \n Статус: активирована ✅\n \n' \
                                                                                                     " Ваш тариф 🧾: (3 месяца, 300 RUB) \n Время оплаты📅:" +
                                                      h[4] + "\n Время окончания⏳:" + h[5], parse_mode='html',
                                                      reply_markup=markupmenuC)
                        elif h[3] == 600:

                            await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                                     bot.get_me()) + '. Ваша подписка  \n Статус: активирована ✅\n \n' \
                                                                                                     " Ваш тариф 🧾: (6 месяцев, 600 RUB) \n Время оплаты📅:" +
                                                      h[4] + "\n Время окончания⏳:" + h[5], parse_mode='html',
                                                      reply_markup=markupmenuC)
                    if h[8] is not None:
                        if h[8] == 1:
                            await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                                     bot.get_me()) + '. Ваша подписка  \n Статус: активирована ✅\n \n' \
                                                                                                     " Ваш тариф 🧾: (1 месяц, 1 EUR) \n Время оплаты📅:" +
                                                      h[4] + "\n Время окончания⏳:" + h[5], parse_mode='html',
                                                      reply_markup=markupmenuC)
                        elif h[8] == 3:
                            await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                                     bot.get_me()) + '. Ваша подписка  \n Статус: активирована ✅\n \n' \
                                                                                                     " Ваш тариф 🧾: (3 месяца, 3 EUR) \n Время оплаты📅:" +
                                                      h[4] + "\n Время окончания⏳:" + h[5], parse_mode='html',
                                                      reply_markup=markupmenuC)
                        elif h[8] == 6:
                            await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                                     bot.get_me()) + '. Ваша подписка  \n Статус: активирована ✅\n \n' \
                                                                                                     " Ваш тариф 🧾: (6 месяцев, 6 EUR) \n Время оплаты📅:" +
                                                      h[4] + "\n Время окончания⏳:" + h[5], parse_mode='html',
                                                      reply_markup=markupmenuC)


                elif datetime.strptime(h[5], '%Y-%m-%d %H:%M:%S.%f') <= daten:  # Подписка неактивна
                    await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                             bot.get_me()) + '. Ваша подписка  \n Статус: неактивирована❌',
                                              parse_mode='html', reply_markup=markupmenuC)
            elif h[5] is None:
                await call.message.answer("Клиент {0.first_name}".format(call.from_user,
                                                                         bot.get_me()) + '. Ваша подписка  \n Статус: неактивирована❌',
                                          parse_mode='html', reply_markup=markupmenuC)







    elif call.data == 'backC':
        await call.message.delete()

        # Покупное меню (оплата)
    if call.data == 'buymenu':
        markupmenuw = types.InlineKeyboardMarkup(resize_keyboard=True)
        bt1 = types.KeyboardButton(" 1 месяц ", callback_data="buytime1")
        bt3 = types.KeyboardButton(" 3 месяца ", callback_data="buytime3")
        bt6 = types.KeyboardButton(" 6 месяцев ", callback_data="buytime6")
        bk = types.KeyboardButton('⬅', callback_data='back')
        markupmenuw.add(bt1, bt3, bt6, bk)
        await call.message.answer("Выберите время действия подписки", reply_markup=markupmenuw)
    elif call.data == 'back':
        await call.message.delete()

        # 1 месяц подписки
    if call.data == 'buytime1':
        markupmenu1 = types.InlineKeyboardMarkup(resize_keyboard=True)
        rub = types.KeyboardButton("Рубли", callback_data="rub1")
        eur = types.KeyboardButton("Евро", callback_data="eur1")
        bk = types.KeyboardButton('⬅', callback_data='back1')
        markupmenu1.add(rub, eur, bk)
        await call.message.answer("Вы выбрали Подписку на 1 месяц. Теперь выберите валюту для оплаты подписки",
                                  reply_markup=markupmenu1)
    elif call.data == 'back1':
        await call.message.delete()

        # 3 месяца подписки
    elif call.data == 'buytime3':
        markupmenu1 = types.InlineKeyboardMarkup(resize_keyboard=True)
        rub = types.KeyboardButton("Рубли", callback_data="rub3")
        eur = types.KeyboardButton("Евро", callback_data="eur3")
        bk = types.KeyboardButton('⬅', callback_data='back1')
        markupmenu1.add(rub, eur, bk)
        await call.message.answer(
            "Вы выбрали Подписку на 3 месяца. Теперь выберите валюту для оплаты подписки",
            reply_markup=markupmenu1)
    elif call.data == 'back1':
        await call.message.delete()

        # 6 месяцев подписки
    elif call.data == 'buytime6':
        markupmenu1 = types.InlineKeyboardMarkup(resize_keyboard=True)
        rub = types.KeyboardButton("Рубли", callback_data="rub6")
        eur = types.KeyboardButton("Евро", callback_data="eur6")
        bk = types.KeyboardButton('⬅', callback_data='back1')
        markupmenu1.add(rub, eur, bk)
        await call.message.answer(
            "Вы выбрали Подписку на 6 месяцев. Теперь выберите валюту для оплаты подписки",
            reply_markup=markupmenu1)
    elif call.data == 'back1':
        await call.message.delete()
        # оплата подписки 1 месяц (руб)
    if config.PAYMENTS_TOKEN.split(':')[1] == 'TEST' and call.data == 'rub1':
        markupmenur1 = types.InlineKeyboardMarkup(resize_keyboard=True)
        bkr1 = types.KeyboardButton('⬅', callback_data='backr1')
        Payr1 = types.KeyboardButton('Оплатить', pay=True)
        markupmenur1.add(Payr1, bkr1)
        amount = PRICE.PRICE1.amount
        await bot.send_invoice(call.message.chat.id,
                               title="Подписка на Закрытую группу",
                               description="Активация подписки",
                               provider_token=config.PAYMENTS_TOKEN,
                               currency="RUB",
                               photo_url="https://sun9-37.userapi.com/impg/U91M8UnuxJv37TiSXJ19qh4gCkdZJp31WATrIg/UVGwNoMJXqQ.jpg?size=320x213&quality=96&sign=7cef1b549b14013701feebf2defde743&c_uniq_tag=5VpH3wDgr1rU7z7g-_QJ4nXfFLgg-h37yz2rhdkB12M&type=album"
                                         "+",
                               photo_width=320,
                               photo_height=213,
                               photo_size=320,
                               is_flexible=False,
                               prices=[LabeledPrice(label='Стоимость подписки', amount=int(amount))],
                               start_parameter="unique-string",
                               payload="test-invoice-payload", reply_markup=markupmenur1)
        await call.message.answer(call.message.chat.id, "Вернуться назад", reply_markup=markupmenur1)
    elif call.data == 'backr1':
        await call.message.delete()
        # оплата подписки 1 месяц (евро)
    if (config.PAYMENTS_TOKEN.split(':')[1] == 'TEST' and call.data == 'eur1'):
        markupmenue1 = types.InlineKeyboardMarkup(resize_keyboard=True)
        bke1 = types.KeyboardButton('⬅', callback_data='backe1')
        Paye1 = types.KeyboardButton('Оплатить', pay=True)
        markupmenue1.add(Paye1, bke1)
        amount = PRICE.PRICE2.amount
        await bot.send_invoice(call.message.chat.id, title="Подписка на Закрытую группу",
                               description="Активация подписки",
                               provider_token=config.PAYMENTS_TOKEN,
                               currency="EUR",
                               photo_url="https://sun9-37.userapi.com/impg/U91M8UnuxJv37TiSXJ19qh4gCkdZJp31WATrIg/UVGwNoMJXqQ.jpg?size=320x213&quality=96&sign=7cef1b549b14013701feebf2defde743&c_uniq_tag=5VpH3wDgr1rU7z7g-_QJ4nXfFLgg-h37yz2rhdkB12M&type=album"
                                         "+",
                               photo_width=320,
                               photo_height=213,
                               photo_size=320,
                               is_flexible=False,
                               prices=[LabeledPrice(label='Стоимость подписки', amount=int(amount))],
                               start_parameter="unique-string",
                               payload="test-invoice-payload", reply_markup=markupmenue1)
        await call.message.answer("Вернуться назад", reply_markup=markupmenue1)
    elif call.data == 'backe1':
        await call.message.delete()

        # оплата подписки 3 месяц (руб)
    if (config.PAYMENTS_TOKEN.split(':')[1] == 'TEST' and call.data == 'rub3'):
        markupmenur3 = types.InlineKeyboardMarkup(resize_keyboard=True)
        bkr1 = types.KeyboardButton('⬅', callback_data='backr1')
        Payr1 = types.KeyboardButton('Оплатить', pay=True)
        markupmenur3.add(Payr1, bkr1)
        amount = PRICE.PRICE3.amount
        await bot.send_invoice(call.message.chat.id,
                               title="Подписка на Закрытую группу",
                               description="Активация подписки",
                               provider_token=config.PAYMENTS_TOKEN,
                               currency="RUB",
                               photo_url="https://sun9-37.userapi.com/impg/U91M8UnuxJv37TiSXJ19qh4gCkdZJp31WATrIg/UVGwNoMJXqQ.jpg?size=320x213&quality=96&sign=7cef1b549b14013701feebf2defde743&c_uniq_tag=5VpH3wDgr1rU7z7g-_QJ4nXfFLgg-h37yz2rhdkB12M&type=album"
                                         "+",
                               photo_width=320,
                               photo_height=213,
                               photo_size=320,
                               is_flexible=False,
                               prices=[LabeledPrice(label='Стоимость подписки', amount=int(amount))],
                               start_parameter="unique-string",
                               payload="test-invoice-payload", reply_markup=markupmenur3)
        await call.message.answer("Вернуться назад", reply_markup=markupmenur3)
    elif call.data == 'backr1':
        await call.message.delete()
        # оплата подписки 6 месяцев (руб)
    if (config.PAYMENTS_TOKEN.split(':')[1] == 'TEST' and call.data == 'rub6'):
        markupmenur6 = types.InlineKeyboardMarkup(resize_keyboard=True)
        bkr1 = types.KeyboardButton('⬅', callback_data='backr1')
        Payr1 = types.KeyboardButton('Оплатить', pay=True)
        markupmenur6.add(Payr1, bkr1)
        amount = PRICE.PRICE6.amount
        await bot.send_invoice(call.message.chat.id,
                               title="Подписка на Закрытую группу",
                               description="Активация подписки",
                               provider_token=config.PAYMENTS_TOKEN,
                               currency="RUB",
                               photo_url="https://sun9-37.userapi.com/impg/U91M8UnuxJv37TiSXJ19qh4gCkdZJp31WATrIg/UVGwNoMJXqQ.jpg?size=320x213&quality=96&sign=7cef1b549b14013701feebf2defde743&c_uniq_tag=5VpH3wDgr1rU7z7g-_QJ4nXfFLgg-h37yz2rhdkB12M&type=album"
                                         "+",
                               photo_width=320,
                               photo_height=213,
                               photo_size=320,
                               is_flexible=False,
                               prices=[LabeledPrice(label='Стоимость подписки', amount=int(amount))],
                               start_parameter="unique-string",
                               payload="test-invoice-payload", reply_markup=markupmenur6)
        await call.message.answer("Вернуться назад", reply_markup=markupmenur6)
    elif call.data == 'backr1':
        await call.message.delete()

        # pre checout (must be answered in 10 seconds)


@dp.pre_checkout_query_handler(lambda query: True)
async def pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_q.id, ok=True)

    # successful payment


@dp.message_handler(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def successful_payment(message: types.Message):
    print("SUCCESSFUL PAYMENT:")
    payment_info = message.successful_payment.to_python()
    for k, v in payment_info.items():
        print(f"{k}={v}")
    await message.answer(text=f"{k}={v}" + '\n Это номер вашей квитанции!\n Сохраните это сообщение в избранное 😉')
    await message.answer(
        f"Платёж на сумму {message.successful_payment.total_amount // 100} {message.successful_payment.currency} прошёл успешно!!!\n Вы можете проверить статус своей подписки в кнопке Статус подписки ")
    await message.answer("Это ваша ссылка для входа в закрытую группу 😊. Удачи!" + config.GROUP_URL)
    count = (message.successful_payment.total_amount // 100)
    print(count)

    if count == 100 or count == 1:
        date1 = datetime.now()
        add1 = timedelta(days=30)
        date2 = date1 + add1
        print(date2)
        subs = 1
        subs_info = f"{k}={v}"

        connect = sqlite3.connect("Datas.db")
        cursor = connect.cursor()

        user_id = message.from_user.id
        user_name = message.from_user.username
        user_firstname = message.from_user.first_name
        cursor.execute(f"""SELECT money_rub, money_eur, users_name, users_firstname, DATE_of_Pay, DATE_of_end_subs, Subs_status, 
        SUBS_INFO
         FROM users WHERE tg_users_id = {user_id} """)
        user_stroke = cursor.fetchone()
        print(user_stroke)
        print(user_stroke[0])
          # Для старых пользователей плюсуем
        if count == 100:
            pricer1 = 100

            cursor.execute(f"""UPDATE users SET money_rub = '{user_stroke[0] + pricer1}', users_name ='{user_name}', users_firstname = '{user_firstname}',
                         DATE_of_Pay = '{date1}', DATE_of_end_subs = '{date2}', Subs_status = '{subs}', SUBS_INFO = '{subs_info}'
                                            WHERE tg_users_id = '{user_id}' """)

        elif count == 1:
            pricee1 = 1

            cursor.execute(f"""UPDATE users SET momey_eur ='{user_stroke[1] + pricee1}', users_name ='{user_name}', users_firstname = '{user_firstname}',
                    DATE_of_Pay = '{date1}', DATE_of_end_subs = '{date2}', Subs_status = '{subs}', SUBS_INFO = '{subs_info}'
                                        WHERE tg_users_id = '{user_id}' """)


        # имя функций, которые дают сюда значения

        connect.commit()
        connect.close()
        await unban()  # Разбан





    elif count == 300 or count == 3:
        date1 = datetime.now()
        add3 = timedelta(days=60)
        date2 = date1 + add3
        print(date2)
        subs = 1
        subs_info = f"{k}={v}"

        connect = sqlite3.connect("Datas.db")
        cursor = connect.cursor()
        user_id = message.from_user.id
        user_name = message.from_user.username
        user_firstname = message.from_user.first_name

        cursor.execute(f"""SELECT money_rub, money_eur, users_name, users_firstname, DATE_of_Pay, DATE_of_end_subs, Subs_status, 
                SUBS_INFO
                 FROM users WHERE tg_users_id = {user_id} """)
        user_stroke = cursor.fetchone()
        if count == 300:
            pricer3 = 300

            cursor.execute(
                f"""UPDATE users SET money_rub = '{user_stroke[0] + pricer3}', users_name ='{user_name}', users_firstname = '{user_firstname}',
                 DATE_of_Pay = '{date1}', DATE_of_end_subs = '{date2}', Subs_status = '{subs}', SUBS_INFO = '{subs_info}'
                                    WHERE tg_users_id = '{user_id}' """)
        elif count == 3:
            pricee3 = 3
            cursor.execute(
                f"""UPDATE users SET momey_eur ='{user_stroke[1] + pricee3}', users_name ='{user_name}', users_firstname = '{user_firstname}',
                                DATE_of_Pay = '{date1}', DATE_of_end_subs = '{date2}', Subs_status = '{subs}', SUBS_INFO = '{subs_info}'
                                                    WHERE tg_users_id = '{user_id}' """)

        # имя функций, которые дают сюда значения

        connect.commit()
        connect.close()
        await unban()  # Разбан



    elif count == 600 or count == 6:
        date1 = datetime.now()
        add6 = timedelta(days=90)
        date2 = date1 + add6
        print(date2)
        subs = 1
        subs_info = f"{k}={v}"

        connect = sqlite3.connect("Datas.db")
        cursor = connect.cursor()
        user_id = message.from_user.id
        user_name = message.from_user.username
        user_firstname = message.from_user.first_name
        cursor.execute(f"""SELECT money_rub, money_eur, users_name, users_firstname, DATE_of_Pay, DATE_of_end_subs, Subs_status, 
                SUBS_INFO
                 FROM users WHERE tg_users_id = {user_id} """)
        user_stroke = cursor.fetchone()
        if count == 600:
            pricer6 = 600

            cursor.execute(
                f"""UPDATE users SET money_rub = '{user_stroke[0] + pricer6}', users_name ='{user_name}', users_firstname = '{user_firstname}',
                             DATE_of_Pay = '{date1}', DATE_of_end_subs = '{date2}', Subs_status = '{subs}', SUBS_INFO = '{subs_info}'
                                                WHERE tg_users_id = '{user_id}' """)
        elif count == 6:
            pricee6 = 6
            cursor.execute(
                f"""UPDATE users SET momey_eur ='{user_stroke[1] + pricee6}', users_name ='{user_name}', users_firstname = '{user_firstname}',
                                DATE_of_Pay = '{date1}', DATE_of_end_subs = '{date2}', Subs_status = '{subs}', SUBS_INFO = '{subs_info}'
                                                    WHERE tg_users_id = '{user_id}' """)
        # имя функций, которые дают сюда значения

        connect.commit()
        connect.close()
        await unban()  # Разбан


# run long-polling
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=False)
