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

# test
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the Telegram Bot token
TOKEN = '6222346347:AAHyDnaolTMOdVQdj9cpQUQR4_4ucl20PWM'

# Create an instance of the bot
bot = telebot.TeleBot(TOKEN)

#os.environ['PGUSER']='postgres'
#os.environ['PGPASSWORD']='CuOuik2xVHTFF33lM4r5'
#os.environ['PGHOST']='containers-us-west-53.railway.app'
#os.environ['PGPORT']='7525'
#os.environ['PGDATABASE']='railway'

def show_gender_keyboard(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard = True)
    male_button = types.KeyboardButton('Мужской')
    female_button = types.KeyboardButton('Женский')
    markup.add(male_button, female_button)
    bot.send_message(chat_id, "Выбери пол:", reply_markup=markup)
    markup_new = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "", reply_markup=markup_new)

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
    except(Exception, Error) as error:
        print(error)
        print('Ошибка 2 при работе с PostgreSQL')
    finally:
        cursor2.close()
        connection2.close()
        show_gender_keyboard(chat_id)
    #if date_valid:
    #    show_video(chat_id)
    #    logger.info('video shown')

@bot.message_handler(func=lambda message: message.text in ['Мужской', 'Женский'])
def handle_gender(message):
    chat_id = message.chat.id

    try:
        connection3 = psycopg2.connect(user=os.getenv('PGUSER'),
                                      password=os.getenv('PGPASSWORD'),
                                      host=os.getenv('PGHOST'),
                                      port=os.getenv('PGPORT'),
                                      database=os.getenv('PGDATABASE'))
        cursor3 = connection3.cursor(cursor_factory=NamedTupleCursor)
        cursor3.execute("SELECT data.search_date from data where chat_id = {}".format(chat_id))
        search_date=cursor3.fetchone()
    except(Exception, Error) as error:
        print(error)
        print('Ошибка 3 при работе с PostgreSQL')
    finally:
        cursor3.close()
        connection3.close()


    try:
        day, month, year = map(int, search_date[0].strftime('%Y-%m-%d').split('-'))

        num = sum_digits(sum_digits(sum_digits(sum_digits(day)) + sum_digits(sum_digits(month)) + sum_digits(sum_digits(year))))
        if message.text == 'Мужской':
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
            cursor3.execute("UPDATE Public.data SET seen = {} WHERE data.chat_id = {}".format(True,chat_id))
            connection3.commit()

        except(Exception, Error) as error:
            print(error)
            print('Ошибка 3.1 при работе с PostgreSQL')
        finally:
            cursor3.close()
            connection3.close()

    except ValueError:
        response = "Введи свою дату рождения в формате *ДД\.ММ\.ГГГГ*"
        bot.send_message(chat_id, response, parse_mode= 'MarkdownV2')

@bot.message_handler(func=lambda message: message.text not in ['Мужской', 'Женский'])
def handle_error(message):
    chat_id = message.chat.id
    response = "Упс\.\.\. что\-то пошло не так\.\.\. Попробуй начать с команды ||_/start_||," \
               " если уже ознакомился с информацией обо мне \- введи свою дату рождения в формате *ДД\.ММ\.ГГГГ*," \
               "а затем выбери свой пол"
    bot.send_message(chat_id, response, parse_mode='MarkdownV2')

#def main():
#    bot.polling(none_stop=True)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(1)
            logger.info(e)