import cherrypy
import telebot
import requests
import hashlib
from telebot import types
from telegram_bot_calendar import WMonthTelegramCalendar
from datetime import date
from dateutil.relativedelta import relativedelta


token = "ХХХХХХХХ"



WEBHOOK_HOST = 'ХХХХХХХХ'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % token

bot = telebot.TeleBot(token)

# Наш вебхук-сервер
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)


# ===============================================================================


@bot.message_handler(commands=["start"])
def start(m):
    user_id = m.from_user.id

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(name) for name in ['Цена туда и обратно', 'Цена в одну сторону']])
    keyboard.add(*[types.KeyboardButton(name) for name in ['ТОП 10 направлений из города']])
    bot.send_message(m.chat.id, 'Выберите действие',
                     reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def message(msg):
    if msg.text == 'Цена туда и обратно':

        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next2)

    elif msg.text == 'Цена в одну сторону':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next4)


    elif msg.text == 'ТОП 10 направлений из города':

        bot.send_message(msg.chat.id, "Укажи город вылета, и я покажу самые популярные направления из этого города за последние 48 часов")
        bot.register_next_step_handler(msg, next3)


# =========================

def next2(msg):
    global city1
    global origin
    city1 = msg.text

    if city1 == 'ТОП 10 направлений из города':
        bot.send_message(msg.chat.id, "Укажи город вылета, и я покажу самые популярные направления из этого города за последние 48 часов")
        bot.register_next_step_handler(msg, next3)

    if city1 == 'Цена туда и обратно':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next2)

    if city1 == 'Цена в одну сторону':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next4)

    if city1 == '/start':
        bot.register_next_step_handler(msg, start)

    if city1 not in ['/start', 'ТОП 10 направлений из города', 'Цена туда и обратно', 'Цена в одну сторону']:
        response = requests.get('https://api.travelpayouts.com/data/ru/cities.json')
        r = response.json()

        for find in r:
            if city1.title() in find['name']:
                origin = find['code']
                bot.send_message(msg.chat.id, "Укажи город прилета")
                bot.register_next_step_handler(msg, cal1data1)
                break

        if city1.title() not in find['name']:
            response = requests.get('https://www.travelpayouts.com/widgets_suggest_params?q=' + city1.title())
            orig = response.json()

            if orig == {}:
                bot.send_message(msg.chat.id, "Возможно в городе/стране допущена ошибка"
                                            "\nПопробуй написать еще раз")
                bot.register_next_step_handler(msg, next2)

            if orig != {}:
                origin = response.json()['capital']['iata']
                bot.send_message(msg.chat.id, "Укажи город прилета")
                bot.register_next_step_handler(msg, cal1data1)





def cal1data1(m):
    global city2
    global destination
    city2 = m.text

    if city2 == 'ТОП 10 направлений из города':
        bot.send_message(m.chat.id, "Укажи город вылета, и я покажу самые популярные направления из этого города за последние 48 часов")
        bot.register_next_step_handler(m, next3)

    if city2 == 'Цена туда и обратно':
        bot.send_message(m.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(m, next2)

    if city2 == 'Цена в одну сторону':
        bot.send_message(m.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(m, next4)

    if city2 == '/start':
        bot.register_next_step_handler(m, start)

    if city2 not in ['/start', 'ТОП 10 направлений из города', 'Цена туда и обратно', 'Цена в одну сторону']:
        response = requests.get('https://api.travelpayouts.com/data/ru/cities.json')
        r = response.json()
        for find in r:
            if city2.title() == find['name']:
                destination = find['code']
                calendar, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=1).build()
                bot.send_message(m.chat.id, "Укажи дату вылета", reply_markup=calendar)
                break

        if city2.title() not in find['name']:
            response = requests.get('https://www.travelpayouts.com/widgets_suggest_params?q=' + city2.title())
            orig = response.json()

            if orig == {}:
                bot.send_message(m.chat.id, "Возможно в городе/стране допущена ошибка"
                                            "\nПопробуй написать еще раз")
                bot.register_next_step_handler(m, cal1data1)

            if orig != {}:
                destination = response.json()['capital']['iata']
                calendar, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=1).build()
                bot.send_message(m.chat.id, "Выберите дату когда летим туда?", reply_markup=calendar)



@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=1))
def cal2data1(c):
    global data1
    result, key, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=1).process(c.data)
    if not result and key:
        bot.edit_message_text("Дата когда летим", c.message.chat.id, c.message.message_id, reply_markup=key)

    elif result:
        data1 = [result]
        bot.edit_message_text(f"Я начал поиск",
                              c.message.chat.id,
                              c.message.message_id)
        calendar, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=2).build()
        bot.send_message(c.message.chat.id, f"Дата когда обратно", reply_markup=calendar)

@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=2))
def сal(c):
    global data2
    result, key, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=2).process(c.data)
    if not result and key:
        bot.edit_message_text("Дата когда обратно",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
    elif result:
        data2 = [result]
        bot.edit_message_text(f"Обратно: {result}",
                              c.message.chat.id,
                              c.message.message_id)


        datax1 = str(data1[0])
        datax2 = str(data2[0])



        marker = '220716'
        host = 'avialos'
        user_ip = '62.217.185.168'
        locale = 'ru'
        trip_class = 'Y'
        adults = '1'
        children = '0'
        infants = '0'
        a = "6aa2a875b4aac40a66e7c5b60c00a832" + ':' + host + ':' + locale + ':' + marker + ':' + datax1 + ':' + destination + ':' + origin + ':' + datax2 + ':' + origin + ':' + destination + ':' + user_ip
        md = hashlib.md5(a.encode('utf-8')).hexdigest()
        d = str(md)
        # туда и обратно
        data = {
            "signature": md,
            "marker": "220716",
            "host": "avialos",
            "user_ip": "62.217.185.168",
            "locale": "ru",
            "segments": [
                {
                    "origin": origin,
                    "destination": destination,
                    "date": datax1
                },
                {
                    "origin": destination,
                    "destination": origin,
                    "date": datax2
                },
            ]
        }

        url = "http://api.travelpayouts.com/v1/flight_search"

        r = requests.post(url, json=data)
        gor = r.json()['search_id']
        my_input = []
        count = 0
        for d in gor:
            d = requests.get('http://api.travelpayouts.com/v1/flight_search_results?uuid=' + gor)
            to = d.json()
            if to == []:
                break
            try:
                go = to[0]['proposals'][0]['terms']
            except KeyError:
                break
            go = to[0]['proposals'][0]['terms']
            for find in go:
                f = go[find]['unified_price']

                my_input.append(f)
                count += 1
                bot.edit_message_text('Придется немного подождать, среднее время поиска 15-30 сек.' + '\nНайдено биллетов: ' + str(count) + '\nАнализирую цены: ' + str(f) + ' руб', c.message.chat.id, c.message.message_id)
                break


        if my_input != []:
                zs = min(my_input)
                urls = 'https://www.aviasales.ru/search?origin_iata=' + origin + '&destination_iata=' + destination + '&depart_date=' + datax1 + '&return_date=' + datax2 + '&with_request=true&adults=1&children=0&infants=0&trip_class=0&locale=ru&one_way=false/r?marker=220716&trs=10474&p=4114'

                keyboard = types.InlineKeyboardMarkup(row_width=2)
                url_button = types.InlineKeyboardButton(text="К билетам", url=urls)
                keyboard.add(url_button)
                bot.send_message(c.message.chat.id, city1.title() + ' - ' + city2.title() +
                                 ' \nТуда ' + datax1 +
                                 ' \nОбратно ' + datax2 +
                                 ' \nЦена: *' + str(zs) + ' руб*', reply_markup=keyboard, parse_mode='Markdown')

        if my_input == []:
                urls = 'https://www.aviasales.ru/search?origin_iata=' + origin + '&destination_iata=' + destination + '&depart_date=' + datax1 + '&return_date=' + datax2 + '&with_request=true&adults=1&children=0&infants=0&trip_class=0&locale=ru&one_way=false/r?marker=220716&trs=10474&p=4114'
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                url_button = types.InlineKeyboardButton(text="К билету", url=urls)
                keyboard.add(url_button)
                bot.send_message(c.message.chat.id,'👇 Цена перелета ниже по ссылке', reply_markup=keyboard, parse_mode= 'Markdown')



# =================

def next3(msg):

    citygor = msg.text

    if citygor == 'ТОП 10 направлений из города':
        bot.send_message(msg.chat.id, "Укажи город вылета, и я покажу самые популярные направления из этого города за последние 48 часов")
        bot.register_next_step_handler(msg, next3)

    if citygor == 'Цена туда и обратно':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next2)

    if citygor == 'Цена в одну сторону':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next4)

    if citygor == '/start':
        bot.register_next_step_handler(msg, start)

    if citygor not in ['/start', 'ТОП 10 направлений из города', 'Цена туда и обратно', 'Цена в одну сторону']:

        response = requests.get('https://api.travelpayouts.com/data/ru/cities.json')
        r = response.json()
        for find in r:
            if citygor.title() == find['name']:
                citygo = find['code']
                break

        if citygor.title() not in find['name']:
            response = requests.get('https://www.travelpayouts.com/widgets_suggest_params?q=' + citygor.title())
            orig = response.json()

            if orig == {}:
                bot.send_message(msg.chat.id, "Возможно в городе/стране допущена ошибка"
                                            "\nПопробуй написать еще раз")
                bot.register_next_step_handler(msg, next3)

            if orig != {}:
                citygo = response.json()['capital']['iata']


        resprice = requests.get(
                    "http://api.travelpayouts.com/v1/city-directions?origin=" + citygo + "&currency=rub&token=6aa2a875b4aac40a66e7c5b60c00a832")
        gor = resprice.json()['data']
        i = 0
        for find in gor:
            if i < 10:
                x = find
                i = i + 1
                res = requests.get('https://api.travelpayouts.com/data/ru/cities.json')
                d = res.json()
                for fi in d:
                    if x in fi['code']:
                        des = fi['name']
                        bot.send_message(msg.chat.id, str(i) + '. ' + des)


# ======================================



def next4(msg):
    global city4
    global origin4
    city4 = msg.text

    if city4 == 'ТОП 10 направлений из города':
        bot.send_message(msg.chat.id, "Укажи город вылета, и я покажу самые популярные направления из этого города за последние 48 часов")
        bot.register_next_step_handler(msg, next3)

    if city4 == 'Цена туда и обратно':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next2)

    if city4 == 'Цена в одну сторону':
        bot.send_message(msg.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(msg, next4)

    if city4 == '/start':
        bot.register_next_step_handler(msg, start)

    if city4 not in ['/start', 'ТОП 10 направлений из города', 'Цена туда и обратно', 'Цена в одну сторону']:
        response = requests.get('https://api.travelpayouts.com/data/ru/cities.json')
        r = response.json()

        for find in r:
            if city4.title() in find['name']:
                origin4 = find['code']
                bot.send_message(msg.chat.id, "Укажи город прилета")
                bot.register_next_step_handler(msg, cal1data4)
                break

        if city4.title() not in find['name']:
            response = requests.get('https://www.travelpayouts.com/widgets_suggest_params?q=' + city4.title())
            orig = response.json()

            if orig == {}:
                bot.send_message(msg.chat.id, "Возможно в городе/стране допущена ошибка"
                                            "\nПопробуй написать еще раз")
                bot.register_next_step_handler(msg, next4)

            if orig != {}:
                origin4 = response.json()['capital']['iata']
                bot.send_message(msg.chat.id, "Укажи город прилета")
                bot.register_next_step_handler(msg, cal1data4)


def cal1data4(m):
    global city5
    global destination4
    city5 = m.text

    if city5 == 'ТОП 10 направлений из города':
        bot.send_message(m.chat.id, "Укажи город вылета, и я покажу самые популярные направления из этого города за последние 48 часов")
        bot.register_next_step_handler(m, next3)

    if city5 == 'Цена туда и обратно':
        bot.send_message(m.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(m, next2)

    if city5 == 'Цена в одну сторону':
        bot.send_message(m.chat.id, "Укажи город вылета")
        bot.register_next_step_handler(m, next4)

    if city5 == '/start':
        bot.register_next_step_handler(m, start)

    if city5 not in ['/start', 'ТОП 10 направлений из города', 'Цена туда и обратно', 'Цена в одну сторону']:
        response = requests.get('https://api.travelpayouts.com/data/ru/cities.json')
        r = response.json()
        for find in r:
            if city5.title() == find['name']:
                destination4 = find['code']
                calendar, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=3).build()
                bot.send_message(m.chat.id, "Укажи дату вылета", reply_markup=calendar)
                break

        if city5.title() not in find['name']:
            response = requests.get('https://www.travelpayouts.com/widgets_suggest_params?q=' + city5.title())
            orig = response.json()

            if orig == {}:
                bot.send_message(m.chat.id, "Возможно в городе/стране допущена ошибка"
                                            "\nПопробуй написать еще раз")
                bot.register_next_step_handler(m, cal1data4)

            if orig != {}:
                destination4 = response.json()['capital']['iata']
                calendar, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=3).build()
                bot.send_message(m.chat.id, "Выберите дату когда летим туда?", reply_markup=calendar)


@bot.callback_query_handler(func=WMonthTelegramCalendar.func(calendar_id=3))
def cal2data1(c):
    global data4
    result, key, step = WMonthTelegramCalendar(min_date=date.today(), max_date=date.today() + relativedelta(years=+1), locale='ru', calendar_id=3).process(c.data)
    if not result and key:
        bot.edit_message_text("Дата когда обратно",
                                  c.message.chat.id,
                                  c.message.message_id,
                                  reply_markup=key)
    elif result:
        data4 = [result]
        bot.edit_message_text(f"Обратно: {result}",
                              c.message.chat.id,
                              c.message.message_id)

        datax1 = str(data4[0])


        marker = '220716'
        host = 'avialos'
        user_ip = '62.217.185.168'
        locale = 'ru'
        trip_class = 'Y'
        adults = '1'
        children = '0'
        infants = '0'
        a = "6aa2a875b4aac40a66e7c5b60c00a832" + ':' + host + ':' + locale + ':' + marker + ':1:0:0' + ':' + datax1 + ':' + destination4 + ':' + origin4 + ':' + 'Y:' + user_ip
        md = hashlib.md5(a.encode('utf-8')).hexdigest()
        d = str(md)
        # туда и обратно
        data = {
            "signature": md,
            "marker": "220716",
            "host": "avialos",
            "user_ip": "62.217.185.168",
            "locale": "ru",
            "trip_class": "Y",
            "passengers": {
                "adults": 1,
                "children": 0,
                "infants": 0
            },
            "segments": [
                {
                    "origin": origin4,
                    "destination": destination4,
                    "date": datax1
                },
            ]
        }

        url = "http://api.travelpayouts.com/v1/flight_search"

        r = requests.post(url, json=data)
        gor = r.json()['search_id']
        my_input = []
        count = 0
        for d in gor:
            d = requests.get('http://api.travelpayouts.com/v1/flight_search_results?uuid=' + gor)
            to = d.json()
            if to == []:
                break
            try:
                go = to[0]['proposals'][0]['terms']
            except KeyError:
                break
            go = to[0]['proposals'][0]['terms']
            for find in go:
                f = go[find]['unified_price']

                my_input.append(f)
                count += 1
                bot.edit_message_text('Придется немного подождать, среднее время поиска 15-30 сек.' + '\nНайдено биллетов: ' + str(count) + '\nАнализирую цены: ' + str(f) + ' руб', c.message.chat.id, c.message.message_id)
                break


        if my_input != []:
                zs = min(my_input)
                urls = 'https://www.aviasales.ru/search?origin_iata=' + origin4 + '&destination_iata=' + destination4 + '&depart_date=' + datax1 + '&with_request=true&adults=1&children=0&infants=0&trip_class=0&locale=ru&one_way=false/r?marker=220716&trs=10474&p=4114'

                keyboard = types.InlineKeyboardMarkup(row_width=2)
                url_button = types.InlineKeyboardButton(text="К билетам", url=urls)
                keyboard.add(url_button)
                bot.send_message(c.message.chat.id, city4.title() + ' - ' + city5.title() +
                                 ' \nТуда ' + datax1 +
                                 ' \nЦена: *' + str(zs) + ' руб*', reply_markup=keyboard, parse_mode='Markdown')

        if my_input == []:
                urls = 'https://www.aviasales.ru/search?origin_iata=' + origin4 + '&destination_iata=' + destination4 + '&depart_date=' + datax1 + '&with_request=true&adults=1&children=0&infants=0&trip_class=0&locale=ru&one_way=false/r?marker=220716&trs=10474&p=4114'
                keyboard = types.InlineKeyboardMarkup(row_width=2)
                url_button = types.InlineKeyboardButton(text="К билету", url=urls)
                keyboard.add(url_button)
                bot.send_message(c.message.chat.id,'👇 Цена перелета ниже по ссылке', reply_markup=keyboard, parse_mode= 'Markdown')




# ===============================================================================

# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
bot.remove_webhook()

# Ставим заново вебхук
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Указываем настройки сервера CherryPy
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

# Собственно, запуск!
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
