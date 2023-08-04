import logging
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import data
import psycopg2
from psycopg2 import Error
from psycopg2.extras import NamedTupleCursor
import os
import datetime
from yookassa import Configuration,Payment
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
import asyncio
from tzlocal import get_localzone

WEEK_LIST = ['Monday', 'Tuesday', 'Wednesday','Thursday','Friday','Saturday','Sunday']
WEEK_DICT = {'Monday':0, 'Tuesday':1, 'Wednesday':2,'Thursday':3,'Friday':4,'Saturday':5,'Sunday':6}

scheduler = AsyncIOScheduler(timezone=str(get_localzone()))

### TEST
#os.environ['ACC_ID']='219009'
#os.environ['KEY']='live_DNLV_Mwuqga6CeMLSQwekNG_K-aWAKYHap_UTBFof8g'
#os.environ['TELEGRAM_TOKEN']='6030183564:AAH1-VdUq3Gu6KvI6SHQa9klkBrGX7Pa9oM'
#os.environ['PGUSER']='postgres'
#os.environ['PGPASSWORD']='CuOuik2xVHTFF33lM4r5'
#os.environ['PGHOST']='containers-us-west-53.railway.app'
#os.environ['PGPORT']='7525'
#os.environ['PGDATABASE']='railway'
#os.environ['ASTROLAB_PRICE'] = '1.00'

Configuration.account_id = os.getenv('ACC_ID')
Configuration.secret_key = os.getenv('KEY')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up the Telegram Bot token
##os.environ['TELEGRAM_TOKEN']='6222346347:AAHyDnaolTMOdVQdj9cpQUQR4_4ucl20PWM'
##os.environ['YOO_TOKEN']='390540012:LIVE:35652'
##os.environ['YOO_TOKEN']='381764678:TEST:60173'
##os.environ['YOO_TOKEN']='381764678:TEST:59224'

# Create an instance of the bot
bot = AsyncTeleBot(os.getenv('TELEGRAM_TOKEN'))

def payment(value,description):
	payment = Payment.create({
    "amount": {
        "value": value,
        "currency": "RUB"
    },
    "confirmation": {
        "type": "redirect",
        "return_url": "https://t.me/AstroLab_bot"
    },
    "capture": True,
    "description": description
	})
	return json.loads(payment.json())

async def check_payment(payment_id):
	payment = json.loads((Payment.find_one(payment_id)).json())
	while payment['status'] == 'pending':
		payment = json.loads((Payment.find_one(payment_id)).json())
		await asyncio.sleep(5)
	if payment['status']=='succeeded':
		logger.info("SUCCSESS RETURN")
		logger.info(payment)
		return True
	else:
		logger.info("BAD RETURN")
		logger.info(payment)
		return False

#async def send_astrovideo(i,video_html):
#    await bot.send_message(i, video_html, parse_mode='HTML')

async def send_day(bot: bot):
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
            await bot.send_message(i,video_html, parse_mode='HTML')
            #for j in ['Monday', 'Tuesday', 'Wednesday','Thursday','Friday','Saturday','Sunday']:
            #await asyncio.sleep(1)
            #await bot.send_message(i, data.description[day_name])
            await asyncio.sleep(3)
            keyboard = types.InlineKeyboardMarkup()
            row1 = [types.InlineKeyboardButton('Получить задание на день', callback_data=day_name)]
            keyboard.add(*row1)
            await bot.send_message(i,'Теорию нужно подкреплять практикой!',reply_markup=keyboard)

            cursor_day.execute("UPDATE Public.astroweek SET \"{}\" = True WHERE astroweek.chat_id = (select data.id from data where chat_id = {})".format(day_name.lower(),i))
            connection_day.commit()

    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка при работе с PostgreSQL')
    finally:
        cursor_day.close()
        connection_day.close()
        await asyncio.sleep(3)

# Function to send multiple images in a single message
async def send_multiple_images(chat_id, image_paths):
    media = []
    for path in image_paths:
        with open(path, 'rb') as file:
            media.append(types.InputMediaPhoto(media=file.read()))
    await bot.send_media_group(chat_id, media)

async def show_gender_keyboard(chat_id):
    keyboard = types.InlineKeyboardMarkup()
    row1 = [types.InlineKeyboardButton('Мужской', callback_data='man'),
            types.InlineKeyboardButton('Женский', callback_data='woman')]
    keyboard.add(*row1)
    await bot.send_message(chat_id, "Выбери пол:", reply_markup=keyboard)
    markup_new = types.ReplyKeyboardRemove()

def sum_digits(n):
   r = 0
   while n:
       r, n = r + n % 10, n // 10
   return r

async def send_pptx(chat_id, caption):
    # Load the video file from the local disk
    with open('Astrolab_Astroweek.pdf', 'rb') as file:
        await bot.send_document(chat_id, file, caption=caption)

async def show_video(chat_id):
    # Load the video file from the local disk
    caption = "Тут могла быть Ваша реклама!"
    with open('IMG_0751.MOV', 'rb') as video_file:
        # Send the video file
        await bot.send_video(chat_id, video_file, caption=caption)

async def show_photo(chat_id,response, file):
    # Load the photo file from the local disk
    with open(file, 'rb') as photo_file:
        # Send the photo file
        await bot.send_photo(chat_id, photo_file, caption=response, parse_mode='MarkdownV2')

# Handle the '/start' command
@bot.message_handler(commands=['start'])
async def start(message):
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
    await bot.send_message(chat_id, response1, parse_mode='MarkdownV2')
    response2 = data.intro_2
    await bot.send_message(chat_id, response2, parse_mode='MarkdownV2')

# Handle date input from users
@bot.message_handler(regexp=r'\d{2}\.\d{2}\.\d{4}')
async def handle_date(message):

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
        await show_gender_keyboard(chat_id)
    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка 2 при работе с PostgreSQL')
    finally:
        cursor2.close()
        connection2.close()
    #if date_valid:
    #    await show_video(chat_id)
    #    logger.info('video shown')

@bot.callback_query_handler(func=lambda call: call.data in ['man','woman'])
async def handle_gender(call: types.CallbackQuery):
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
        await bot.send_message(chat_id, "А еще больше в аккууте инстагарам\! \n https://instagram\.com/evgenia\.astrolab", parse_mode='MarkdownV2')
    try:
        day, month, year = map(int, search_date[0].strftime('%Y-%m-%d').split('-'))

        num = sum_digits(sum_digits(sum_digits(sum_digits(day)) + sum_digits(sum_digits(month)) + sum_digits(sum_digits(year))))
        if call.data == 'man':
            response = data.planetsM[num]
            file = data.picturesM[num]
        else:
            response = data.planetsF[num]
            file = data.picturesF[num]
        await show_photo(chat_id, response, file)

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
            await bot.send_message(chat_id, video_html, parse_mode='HTML')

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
        await bot.send_message(chat_id, response, parse_mode= 'MarkdownV2')
    finally:
        await asyncio.sleep(3)
        if id == None:
            keyboard = types.InlineKeyboardMarkup()
            row1 = [types.InlineKeyboardButton('Получить доступ к ASTROWEEK!', callback_data='astroweek')]
            row2 = [types.InlineKeyboardButton('Посмотрет отзывы', callback_data='comments')]
            row3 = [types.InlineKeyboardButton('Позже', callback_data='later')]
            keyboard.add(*row1)
            keyboard.add(*row2)
            keyboard.add(*row3)
            await asyncio.sleep(10)
            await bot.send_message(chat_id, data.astroweek,reply_markup=keyboard, parse_mode= 'MarkdownV2')
        else:
            await bot.send_message(chat_id, data.later, parse_mode='MarkdownV2')
        await bot.delete_message(chat_id, call.message.message_id)

    #else:
    #    bot.send_message(chat_id, "XXX", parse_mode='MarkdownV2')

@bot.message_handler(func=lambda message: True)
async def handle_error(message):
    chat_id = message.chat.id
    response = "Упс\.\.\. что\-то пошло не так\.\.\. Попробуй начать с команды ||_/start_||," \
               " если уже ознакомился с информацией обо мне \- введи свою дату рождения в формате *ДД\.ММ\.ГГГГ*," \
               "а затем выбери свой пол"
    await bot.send_message(chat_id, response, parse_mode='MarkdownV2')

@bot.callback_query_handler(func= lambda call: call.data == 'astroweek')
async def astroweek(call: types.CallbackQuery):
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
        await bot.send_message(chat_id,'Ссылка на оплату: \n'+(payment_deatils['confirmation'])['confirmation_url']+'\n Если возникли вопросы по оплате, пиши напрямую @evgenia_astrolab')
        if await check_payment(payment_deatils['id']):
            #call.message.answer("платеж")
            await bot.send_message(chat_id,"Оплата прошла успешно!")
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
                await bot.send_message(chat_id, video_html, parse_mode='HTML')
                await bot.send_message(chat_id, data.description['Start'], parse_mode='MarkdownV2')
                keyboard = types.InlineKeyboardMarkup()
                row1 = [types.InlineKeyboardButton('Открыть полный доступ к курсу сейчас', callback_data='Monday-now')]
                row2 = [types.InlineKeyboardButton('Начать с ближайшего понедельника', callback_data='days')]
                keyboard.add(*row1)
                keyboard.add(*row2)
                await asyncio.sleep(5)
                await bot.send_message(chat_id, data.selection, reply_markup=keyboard, parse_mode='MarkdownV2')
            except(Exception, Error) as error:
                logger.info(error)
                print(error)
                print('Ошибка 4 при работе с PostgreSQL')
            finally:
                cursor4.close()
                connection4.close()
                await asyncio.sleep(3)
        else:
            #call.message.answer("платеж не прошел")
            await bot.send_message(chat_id,'Оплата не удалась, попробуй еще раз или обратись в поддержку!')
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
        await bot.send_message(chat_id,'Похоже, ты уже приобрел доступ к Astroweek. Если первое видео еще не пришло, жди его в ближайший понедельник!')

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

@bot.callback_query_handler(func= lambda call: call.data.split('-')[-1] == 'now')
async def astroweek_now(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    i = call.data.split('-')[0]
    try:
        connection7 = psycopg2.connect(user=os.getenv('PGUSER'),
                                       password=os.getenv('PGPASSWORD'),
                                       host=os.getenv('PGHOST'),
                                       port=os.getenv('PGPORT'),
                                       database=os.getenv('PGDATABASE'))
        cursor7 = connection7.cursor(cursor_factory=NamedTupleCursor)
        youtube_link = data.astro_video[i]
        video_html = f'<a href="{youtube_link}">' + i + '</a>'
        await bot.send_message(chat_id, video_html, parse_mode='HTML')
        # for j in ['Monday', 'Tuesday', 'Wednesday','Thursday','Friday','Saturday','Sunday']:
        #await asyncio.sleep(1)
        await bot.send_message(chat_id, data.description[i])
        await asyncio.sleep(3)

        keyboard = types.InlineKeyboardMarkup()
        row1 = [types.InlineKeyboardButton('Получить задание на день', callback_data=i)]
        keyboard.add(*row1)
        await bot.send_message(chat_id, 'Теорию нужно подкреплять практикой!', reply_markup=keyboard)

        cursor7.execute("UPDATE Public.astroweek SET \"{}\" = True WHERE astroweek.chat_id = (select data.id from data where chat_id = {})".format(i.lower(), chat_id))
        connection7.commit()

    except(Exception, Error) as error:
        logger.info(error)
        print(error)
        print('Ошибка 7 при работе с PostgreSQL')
    finally:
        cursor7.close()
        connection7.close()
    await bot.delete_message(chat_id, call.message.message_id)
    #await bot.send_message(chat_id, 'Жди новые продукты!')

@bot.callback_query_handler(func= lambda call: call.data == 'days')
async def astroweek_later(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    await bot.send_message(chat_id, 'А пока ты можешь делать запросы по дате рождения', parse_mode='MarkdownV2')
    await bot.delete_message(chat_id, call.message.message_id)

@bot.callback_query_handler(func= lambda call: call.data == 'later')
async def later_func(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    #bot.delete_message(chat_id, call.message.message_id)
    await bot.send_message(chat_id, data.later, parse_mode= 'MarkdownV2')

@bot.callback_query_handler(func= lambda call: call.data in ['comments'])
async def comments_func(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    #bot.delete_message(chat_id, call.message.message_id)
    await send_multiple_images(chat_id,data.picture_paths)
    await asyncio.sleep(3)
    keyboard = types.InlineKeyboardMarkup()
    row1 = [types.InlineKeyboardButton('Получить доступ к ASTROWEEK!', callback_data='astroweek')]
    row3 = [types.InlineKeyboardButton('Позже', callback_data='later')]
    keyboard.add(*row1)
    keyboard.add(*row3)
    await asyncio.sleep(3)
    await bot.send_message(chat_id,'Присоединяйся к ASTROWEEK, по всем интересующим вопросам пиши @evgenia_astrolab', reply_markup=keyboard)

@bot.callback_query_handler(func= lambda call: call.data in WEEK_LIST)
async def tasks (call: types.CallbackQuery):
    chat_id = call.message.chat.id

    await bot.delete_message(chat_id, call.message.message_id)

    await bot.send_message(chat_id, data.tasks[call.data], parse_mode='MarkdownV2')

    await asyncio.sleep(3)
    if call.data == 'Sunday':
        await asyncio.sleep(2)
        youtube_link = "https://www.youtube.com/playlist?list=PLRzFzh4t3pDxlSlBGr4-FfA9UIIZ9-Xl9"
        video_html = f'<a href="{youtube_link}"></a>'
        await send_pptx(chat_id, 'Курс подошел к концу. Эта шпаргалка поможет в будущем. Все видео ты сможешь найти в плейлисте')
        await bot.send_message(chat_id,video_html, parse_mode='HTML')

    else:
        keyboard = types.InlineKeyboardMarkup()
        row1 = [types.InlineKeyboardButton('Следующий день!', callback_data=WEEK_LIST[WEEK_DICT[call.data]+1] + '-now')]
        keyboard.add(*row1)
        await bot.send_message(chat_id, 'Если все задания выполнены, можешь переходить к следующему дню! Или дождаться следующего дня недели для полноты погружения 💫', reply_markup=keyboard)

async def run_bot():
    # Start the bot polling
    scheduler.add_job(send_day,'cron', day_of_week='mon-sun', hour=9, minute=0, args=(bot,))
    scheduler.start()
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    while True:
        try:
            asyncio.run(run_bot())
        except Exception as e:
            logger.info(e)