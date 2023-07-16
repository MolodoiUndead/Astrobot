import logging
import telebot
import time
from telebot import types
import data
import psycopg2
from psycopg2 import Error
from psycopg2.extras import NamedTupleCursor
import os
import datetime
from yookassa import Configuration,Payment
import schedule
from threading import Thread
import uuid
import json
import asyncio
from telebot import apihelper

Configuration.account_id = os.getenv('ACC_ID')
#'219009'
Configuration.secret_key = os.getenv('KEY')
#'live_DNLV_Mwuqga6CeMLSQwekNG_K-aWAKYHap_UTBFof8g'

# test
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the Telegram Bot token
#os.environ['TELEGRAM_TOKEN']='6222346347:AAHyDnaolTMOdVQdj9cpQUQR4_4ucl20PWM'
#os.environ['YOO_TOKEN']='390540012:LIVE:35652'

##os.environ['TELEGRAM_TOKEN']='6030183564:AAH1-VdUq3Gu6KvI6SHQa9klkBrGX7Pa9oM'
##os.environ['YOO_TOKEN']='381764678:TEST:60173'
##os.environ['YOO_TOKEN']='381764678:TEST:59224'
#os.environ['PGUSER']='postgres'
#os.environ['PGPASSWORD']='CuOuik2xVHTFF33lM4r5'
#os.environ['PGHOST']='containers-us-west-53.railway.app'
#os.environ['PGPORT']='7525'
#os.environ['PGDATABASE']='railway'
#os.environ['ASTROLAB_PRICE'] = 100

# Create an instance of the bot
bot = telebot.TeleBot(os.getenv('TELEGRAM_TOKEN'))

def payment(value,description):
	payment = Payment.create({
    "amount": {
        "value": value,
        "currency": "RUB"
    },
    "payment_method_data": {
        "type": "sberbank"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://t.me/AstroLab_bot"
    },
    "capture": True,
    "description": description
	})
	return json.loads(payment.json())

def check_payment(payment_id):
	payment = json.loads((Payment.find_one(payment_id)).json())
	while payment['status'] == 'pending':
		payment = json.loads((Payment.find_one(payment_id)).json())
		time.sleep(5)
	if payment['status']=='succeeded':
		logger.info("SUCCSESS RETURN")
		logger.info(payment)
		return True
	else:
		logger.info("BAD RETURN")
		logger.info(payment)
		return False

def send_day():
    day_name = datetime.date.today()
    day_name = day_name.strftime("%A")
    try:
        connection_day = psycopg2.connect(user=os.getenv('PGUSER'),
                                          password=os.getenv('PGPASSWORD'),
                                          host=os.getenv('PGHOST'),
                                          port=os.getenv('PGPORT'),
                                          database=os.getenv('PGDATABASE'))
        cursor_day = connection_day.cursor(cursor_factory=NamedTupleCursor)
        if day_name.lower() != 'monday':
            cursor_day.execute("SELECT data.chat_id from data WHERE data.id in (select chat_id from public.astroweek  where \"monday\" is True and \"{}\" is False)".format(day_name.lower()))
        else:
            cursor_day.execute("SELECT data.chat_id from data WHERE data.id in (select chat_id from public.astroweek  where \"{}\" is False)".format(day_name.lower()))
        list = [r[0] for r in cursor_day.fetchall()]

        youtube_link = data.astro_video[day_name]
        video_html = f'<a href="{youtube_link}">'+day_name+'</a>'
        for i in list:
            bot.send_message(i, video_html, parse_mode='HTML')
            cursor_day.execute("UPDATE Public.astroweek SET \"{}\" = True WHERE astroweek.chat_id = (select data.id from data where chat_id = {})".format(day_name.lower(),i))
            connection_day.commit()
    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка day при работе с PostgreSQL')
    finally:
        cursor_day.close()
        connection_day.close()

# Function to send multiple images in a single message
def send_multiple_images(chat_id, image_paths):
    media = []
    for path in image_paths:
        with open(path, 'rb') as file:
            media.append(types.InputMediaPhoto(media=file.read()))
    bot.send_media_group(chat_id, media)

def show_gender_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    row1 = [types.InlineKeyboardButton('Мужской', callback_data='man'),
            types.InlineKeyboardButton('Женский', callback_data='woman')]
    keyboard.add(*row1)
    bot.send_message(chat_id, "Выбери пол:", reply_markup=keyboard)
    markup_new = types.ReplyKeyboardRemove()

def sum_digits(n):
   r = 0
   while n:
       r, n = r + n % 10, n // 10
   return r

def show_video(chat_id):
    # Load the video file from the local disk
    caption = "Тут могла быть Ваша реклама!"
    with open('IMG_0751.MOV', 'rb') as video_file:
        # Send the video file
        bot.send_video(chat_id, video_file, caption=caption)

def show_photo(chat_id,response, file):
    # Load the photo file from the local disk
    with open(file, 'rb') as photo_file:
        # Send the photo file
        bot.send_photo(chat_id, photo_file, caption=response, parse_mode='MarkdownV2')

# Handle the '/start' command
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    try:
        connection1 = psycopg2.connect(user=os.getenv('PGUSER'),
                                      password=os.getenv('PGPASSWORD'),
                                      host=os.getenv('PGHOST'),
                                      port=os.getenv('PGPORT'),
                                      database=os.getenv('PGDATABASE'))
        cursor1 = connection1.cursor(cursor_factory=NamedTupleCursor)
        cursor1.execute("SELECT data.chat_id from data WHERE data.chat_id = {}".format(chat_id))
        date = cursor1.fetchall()
        if len(date) < 1:
            cursor1.execute(
                "INSERT INTO Public.data (first_name, last_name, user_id, username, chat_id) VALUES ('{}','{}',{},'{}',{});".format(
                    message.from_user.first_name, message.from_user.last_name,
                    message.from_user.id,message.from_user.username,chat_id))
            connection1.commit()

    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка 1 при работе с PostgreSQL')
    finally:
        cursor1.close()
        connection1.close()
    response1 = data.intro
    bot.send_message(chat_id, response1, parse_mode='MarkdownV2')
    response2 = data.intro_2
    bot.send_message(chat_id, response2, parse_mode='MarkdownV2')

# Handle date input from users
@bot.message_handler(regexp=r'\d{2}\.\d{2}\.\d{4}')
def handle_date(message):

    chat_id = message.chat.id
    search_date = message.text.strip()
    search_date = datetime.datetime.strptime(search_date, "%d.%m.%Y").strftime("%Y-%m-%d")
    try:
        connection2 = psycopg2.connect(user=os.getenv('PGUSER'),
                                      password=os.getenv('PGPASSWORD'),
                                      host=os.getenv('PGHOST'),
                                      port=os.getenv('PGPORT'),
                                      database=os.getenv('PGDATABASE'))
        cursor2 = connection2.cursor(cursor_factory=NamedTupleCursor)

        cursor2.execute("UPDATE Public.data SET search_date = '{}' WHERE data.chat_id = {}".format(search_date,chat_id))
        connection2.commit()
        show_gender_keyboard(chat_id)
    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка 2 при работе с PostgreSQL')
    finally:
        cursor2.close()
        connection2.close()
    #if date_valid:
    #    show_video(chat_id)
    #    logger.info('video shown')

@bot.callback_query_handler(func=lambda call: call.data in ['man','woman'])
def handle_gender(call: types.CallbackQuery):
    chat_id = call.message.chat.id

    try:
        connection3 = psycopg2.connect(user=os.getenv('PGUSER'),
                                      password=os.getenv('PGPASSWORD'),
                                      host=os.getenv('PGHOST'),
                                      port=os.getenv('PGPORT'),
                                      database=os.getenv('PGDATABASE'))
        cursor3 = connection3.cursor(cursor_factory=NamedTupleCursor)
        cursor3.execute("SELECT data.search_date from data where chat_id = {}".format(chat_id))
        search_date=cursor3.fetchone()
        cursor3.execute("SELECT data.seen from data where chat_id = {}".format(chat_id))
        seen = cursor3.fetchone()[0]
    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка 3 при работе с PostgreSQL')
    finally:
        cursor3.close()
        connection3.close()

    if seen > 4:
        bot.send_message(chat_id, "А еще больше в аккууте инстагарам\! \n https://instagram\.com/evgenia\.astrolab", parse_mode='MarkdownV2')
    try:
        day, month, year = map(int, search_date[0].strftime('%Y-%m-%d').split('-'))

        num = sum_digits(sum_digits(sum_digits(sum_digits(day)) + sum_digits(sum_digits(month)) + sum_digits(sum_digits(year))))
        if call.data == 'man':
            response = data.planetsM[num]
            file = data.picturesM[num]
        else:
            response = data.planetsF[num]
            file = data.picturesF[num]
        show_photo(chat_id, response, file)

        # Get the highest quality video stream using pytube
        #video = pytube.YouTube('https://youtu.be/Up1U-4pibKU')
        #video_stream = video.streams.get_highest_resolution()
        #video_stream = video.streams.filter(file_extension='mp4',res='360p').first()
        #print(video.streams)
        #video_url = video_stream.url

        # Send the video by URL
        #bot.send_video(chat_id, video_url)

        if seen < 1:
            youtube_link = "https://www.youtube.com/watch?v=QFIpBjZfsG0"
            video_html = f'<a href="{youtube_link}">Evgenia AstroLab</a>'
            bot.send_message(chat_id, video_html, parse_mode='HTML')

        try:
            connection3 = psycopg2.connect(user=os.getenv('PGUSER'),
                                           password=os.getenv('PGPASSWORD'),
                                           host=os.getenv('PGHOST'),
                                           port=os.getenv('PGPORT'),
                                           database=os.getenv('PGDATABASE'))
            cursor3 = connection3.cursor(cursor_factory=NamedTupleCursor)
            cursor3.execute("UPDATE Public.data SET seen = {} WHERE data.chat_id = {}".format(seen + 1,chat_id))
            connection3.commit()
            cursor3.execute(
                "SELECT chat_id from astroweek where astroweek.chat_id = (select id from public.data where data.chat_id = {})".format(
                    chat_id))
            id = cursor3.fetchone()
        except(Exception, Error) as error:
            logger.info(error)
            print(error)
            print('Ошибка 3.1 при работе с PostgreSQL')
        finally:
            cursor3.close()
            connection3.close()

    except ValueError:
        response = "Введи свою дату рождения в формате *ДД\.ММ\.ГГГГ*"
        bot.send_message(chat_id, response, parse_mode= 'MarkdownV2')
    finally:
        time.sleep(1)
        if id == None:
            keyboard = types.InlineKeyboardMarkup()
            row1 = [types.InlineKeyboardButton('Получить доступ к ASTROWEEK!', callback_data='astroweek')]
            row2 = [types.InlineKeyboardButton('Посмотрет отзывы', callback_data='comments')]
            row3 = [types.InlineKeyboardButton('Позже', callback_data='later')]
            keyboard.add(*row1)
            keyboard.add(*row2)
            keyboard.add(*row3)
            time.sleep(10)
            bot.send_message(chat_id, data.astroweek,reply_markup=keyboard, parse_mode= 'MarkdownV2')
        else:
            bot.send_message(chat_id, data.later, parse_mode='MarkdownV2')
        bot.delete_message(chat_id, call.message.message_id)

    #else:
    #    bot.send_message(chat_id, "XXX", parse_mode='MarkdownV2')

@bot.message_handler(func=lambda message: True)
def handle_error(message):
    chat_id = message.chat.id
    response = "Упс\.\.\. что\-то пошло не так\.\.\. Попробуй начать с команды ||_/start_||," \
               " если уже ознакомился с информацией обо мне \- введи свою дату рождения в формате *ДД\.ММ\.ГГГГ*," \
               "а затем выбери свой пол"
    bot.send_message(chat_id, response, parse_mode='MarkdownV2')

@bot.callback_query_handler(func= lambda call: call.data == 'astroweek')
def astroweek(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    id = []
    try:
        connection4 = psycopg2.connect(user=os.getenv('PGUSER'),
                                       password=os.getenv('PGPASSWORD'),
                                       host=os.getenv('PGHOST'),
                                       port=os.getenv('PGPORT'),
                                       database=os.getenv('PGDATABASE'))
        cursor4 = connection4.cursor(cursor_factory=NamedTupleCursor)
        cursor4.execute("SELECT chat_id from astroweek where astroweek.chat_id = (select id from public.data where data.chat_id = {})".format(chat_id))
        id = cursor4.fetchone()
    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка 4 при работе с PostgreSQL')
    finally:
        cursor4.close()
        connection4.close()
    #bot.delete_message(chat_id, call.message.message_id)
    if id == None:
        #call.message.answer('Оплата марафона')
        payment_deatils = payment(os.getenv('ASTROLAB_PRICE'), 'Доступ к ASTROWEEK')
        #call.message.answer((payment_deatils['confirmation'])['confirmation_url'])
        bot.send_message(chat_id,'Ссылка на оплату: \n'+(payment_deatils['confirmation'])['confirmation_url'])
        if check_payment(payment_deatils['id']):
            #call.message.answer("платеж")
            bot.send_message(chat_id,"Оплата прошла успешно!")
            try:
                connection4 = psycopg2.connect(user=os.getenv('PGUSER'),
                                               password=os.getenv('PGPASSWORD'),
                                               host=os.getenv('PGHOST'),
                                               port=os.getenv('PGPORT'),
                                               database=os.getenv('PGDATABASE'))
                cursor4 = connection4.cursor(cursor_factory=NamedTupleCursor)
                cursor4.execute(
                    "INSERT INTO Public.astroweek (chat_id) VALUES ((select id from public.data where data.chat_id = {}));".format(
                        chat_id))
                connection4.commit()
                youtube_link = data.astro_video['Start']
                video_html = f'<a href="{youtube_link}">' + 'Введение' + '</a>'
                bot.send_message(chat_id, video_html, parse_mode='HTML')
            except(Exception, Error) as error:
                logger.info(error)
                print(error)
                print('Ошибка 4 при работе с PostgreSQL')
            finally:
                cursor4.close()
                connection4.close()
        else:
            #call.message.answer("платеж не прошел")
            bot.send_message(chat_id,'Оплата не удалась, попробуй еще раз или обратись в поддержку!')
        '''bot.send_message(chat_id,'https://yookassa.ru/my/i/ZLQIyDX6rGTs/l')
        bot.send_invoice(chat_id=chat_id,
                         title='ASTROWEEK',
                         description='Полный доступ к недельному марафону',
                         invoice_payload='astroweek',
                         provider_token=os.getenv('YOO_TOKEN'),
                         currency='RUB',
                         start_parameter='astroweek',
                         prices=[types.LabeledPrice(label='astroweek', amount=10000)])'''
    else:
        bot.send_message(chat_id,'Похоже, ты уже приобрел доступ к Astroweek. Если первое видео еще не пришло, жди его в ближайший понедельник!')

'''@bot.pre_checkout_query_handler(func=lambda query: True)
def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def process_pay(message: types.Message):
    chat_id = message.chat.id
    logger.info(message.successful_payment.order_info)
    if message.successful_payment.invoice_payload == 'astroweek':
        try:
            connection4 = psycopg2.connect(user=os.getenv('PGUSER'),
                                           password=os.getenv('PGPASSWORD'),
                                           host=os.getenv('PGHOST'),
                                           port=os.getenv('PGPORT'),
                                           database=os.getenv('PGDATABASE'))
            cursor4 = connection4.cursor(cursor_factory=NamedTupleCursor)
            cursor4.execute("INSERT INTO Public.astroweek (chat_id) VALUES ((select id from public.data where data.chat_id = {}));".format(chat_id))
            connection4.commit()
            youtube_link = data.astro_video['Start']
            video_html = f'<a href="{youtube_link}">' + 'Введение' + '</a>'
            bot.send_message(chat_id, video_html, parse_mode='HTML')
        except(Exception, Error) as error:
            logger.info(error)
            print(error)
            print('Ошибка 4 при работе с PostgreSQL')
        finally:
            cursor4.close()
            connection4.close()'''

@bot.callback_query_handler(func= lambda call: call.data == 'later')
def later_func(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    #bot.delete_message(chat_id, call.message.message_id)
    bot.send_message(chat_id, data.later, parse_mode= 'MarkdownV2')

@bot.callback_query_handler(func= lambda call: call.data == 'comments')
def comments_func(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    #bot.delete_message(chat_id, call.message.message_id)
    send_multiple_images(chat_id,data.picture_paths)
    time.sleep(3)
    bot.send_message(chat_id, data.later, parse_mode='MarkdownV2')

def schedule_checker():
    while True:
        schedule.run_pending()
        time.sleep(1)

def run_bot():
    # Start the bot polling
    Thread(target=schedule_checker).start()
    bot.polling(none_stop=True)

if __name__ == '__main__':
    schedule.every().day.at('09:00').do(send_day)
    while True:
        try:
            run_bot()
        except Exception as e:
            time.sleep(1)
            logger.info(e)