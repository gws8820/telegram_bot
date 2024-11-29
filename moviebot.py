import os
import logging
import requests
import telegram
from telegram.ext import ContextTypes, Application
from telegram.request import HTTPXRequest
from bs4 import BeautifulSoup
from dotenv import load_dotenv


logging.basicConfig(filename='moviebot_error.log', level=logging.ERROR)
load_dotenv()

token = os.getenv('MOVIE_API_TOKEN')
chat_id = os.getenv('MOVIE_CHAT_ID')
bot = telegram.Bot(token=token, request=HTTPXRequest(http_version='1.1'))

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}
cur1_url = None
cur2_url = None

async def send_msg(up_url, up_title):
    await bot.send_message(chat_id, f'{up_title}\n{up_url}')

async def callback(context: ContextTypes.DEFAULT_TYPE):
    url1 = 'https://extmovie.com/?_filter=search&act=&vid=&mid=movietalk&category=&search_target=title_content&search_keyword=%EC%98%A4%EB%8A%98%EC%9D%98+%EC%BF%A0%ED%8F%B0'
    try:
        html1 = requests.get(url1, headers=header).text
        soup1 = BeautifulSoup(html1, 'html.parser')
        up1 = soup1.find('div', 'article_type').parent.select('a.title_link')[0]
        up1_title = up1.text.strip()
        up1_url = f'https://extmovie.com{up1["href"].split("?")[0]}'
    except Exception as e:
        logging.error(f"Error fetching data from url1: {e}")
        return

    url2 = 'https://extmovie.com/?_filter=search&act=&vid=&mid=bestboard&category=&search_target=title_content&search_keyword=%ED%95%A0%EC%9D%B8'
    try:
        html2 = requests.get(url2, headers=header).text
        soup2 = BeautifulSoup(html2, 'html.parser')
        up2 = soup2.find('div', 'article_type').parent.select('a.title_link')[0]
        up2_title = up2.text.strip()
        up2_url = f'https://extmovie.com{up2["href"].split("?")[0]}'
    except Exception as e:
        logging.error(f"Error fetching data from url2: {e}")
        return

    global cur1_url, cur2_url

    if cur1_url != up1_url:
        cur1_url = up1_url
        await send_msg(up1_url, up1_title)
        if up1_url != up2_url:  # URL1 solely updated
            pass
        else:  # url1, url2 # Both url1 and url2 updated
            cur2_url = up2_url
    elif cur2_url != up2_url:  # Url2 solely updated
        cur2_url = up2_url
        await send_msg(up2_url, up2_title)
    else:  # No update
        logging.info('No Update')

application = Application.builder().token(token).build()
application.job_queue.run_repeating(callback, interval=60)
application.run_polling()
