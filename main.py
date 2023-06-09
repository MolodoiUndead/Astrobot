import logging
import telebot
import time
from telebot import types
import data
import json


# test
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the Telegram Bot token
TOKEN = '6222346347:AAHyDnaolTMOdVQdj9cpQUQR4_4ucl20PWM'

# Create an instance of the bot
bot = telebot.TeleBot(TOKEN)

with open('dictionary.json') as json_file:
    user_data = json.load(json_file)

def show_gender_keyboard(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2, one_time_keyboard=True, resize_keyboard = True)
    male_button = types.KeyboardButton('Мужской')
    female_button = types.KeyboardButton('Женский')
    markup.add(male_button, female_button)
    bot.send_message(chat_id, "Выбери пол:", reply_markup=markup)

def sum_digits(n):
   r = 0
   while n:
       r, n = r + n % 10, n // 10
   return r

def show_video(chat_id):
    # Load the video file from the local disk
    caption = "Тут могла быть Ваша реклама!"
    with open('C:/Users/ромазавр/astrobot/IMG_0751.MOV', 'rb') as video_file:
        # Send the video file
        bot.send_video(chat_id, video_file, caption=caption)

def show_photo(chat_id,response, file):
    # Load the photo file from the local disk
    with open('C:/Users/ромазавр/astrobot/'+file, 'rb') as photo_file:
        # Send the photo file
        bot.send_photo(chat_id, photo_file, caption=response, parse_mode='MarkdownV2')


# Handle the '/start' command
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    response1 = "Добро пожаловать в бота команды Astro Lab!"
    bot.send_message(chat_id, response1)
    response2 = "Введи свою дату рождения в формате ДД.ММ.ГГГГ и узнай свой базовый талант и возможности."
    bot.send_message(chat_id, response2)

# Handle date input from users
@bot.message_handler(regexp=r'\d{2}\.\d{2}\.\d{4}')
def handle_date(message):
    with open('dictionary.json') as json_file:
        user_data = json.load(json_file)
    chat_id = message.chat.id
    birthday = message.text.strip()
    # Perform date validation

    user_data[str(chat_id)] = {'birthday': birthday}
    with open('dictionary.json', 'w') as json_file:
        json.dump(user_data, json_file)
    show_gender_keyboard(chat_id)

    #if date_valid:
    #    show_video(chat_id)
    #    logger.info('video shown')

@bot.message_handler(func=lambda message: message.text in ['Мужской', 'Женский'])
def handle_gender(message):
    chat_id = message.chat.id
    with open('dictionary.json') as json_file:
        user_data = json.load(json_file)
    birthday = str(user_data[str(chat_id)]['birthday'])

    try:
        day, month, year = map(int, birthday.split('.'))


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


        youtube_link = "https://www.youtube.com/watch?v=4tAKZb5N_CA"
        video_html = f'<a href="{youtube_link}">AstroLab</a>'
        bot.send_message(chat_id, video_html, parse_mode='HTML')
    except ValueError:
        response = "Введи свою дату рождения в формате ДД.ММ.ГГГГ"
        bot.send_message(chat_id, response, parse_mode= 'MarkdownV2')

#def main():
#    bot.polling(none_stop=True)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            with open('dictionary.json', 'w') as json_file:
                json.dump(user_data, json_file)
            time.sleep(1)
            logger.info(e)