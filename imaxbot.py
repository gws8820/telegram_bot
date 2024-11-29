import os
import logging
import telegram
from telegram.ext import ContextTypes, ApplicationBuilder
from telegram.request import HTTPXRequest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv


logging.basicConfig(filename='imaxbot_error.log', level=logging.ERROR)
load_dotenv()

token = os.getenv('IMAX_API_TOKEN')
chat_id = os.getenv('IMAX_CHAT_ID')
bot = telegram.Bot(token=token, request=HTTPXRequest(http_version='1.1'))
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'}

currentdate = "19700101"

async def send_msg(up_date, movielist):
    try:
        await bot.send_message(chat_id, f'업데이트 : *{up_date}*\nhttp://www.cgv.co.kr/ticket/\n\n영화 목록\n--------------------{movielist}', "markdown")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

async def callback(context: ContextTypes.DEFAULT_TYPE):
    global currentdate
    movielist = ''

    svc = Service('/usr/lib/chromium-browser/chromedriver')
    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = "/usr/lib/chromium-browser/chromium-browser"
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-default-apps')
    chrome_options.add_argument('--disable-sync')
    chrome_options.add_argument('--no-first-run')
    chrome_options.add_argument('--no-default-browser-check')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(service=svc, options=chrome_options)
    try:
        driver.get("http://www.cgv.co.kr/ticket/")
        driver.switch_to.frame("ticket_iframe")
        wait = WebDriverWait(driver, 30)  # 최대 30초까지 대기

        # 버튼 1 클릭
        button1 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ticket"]/div[2]/div[1]/div[2]//a[text()="특별관"]')))
        button1.click()

        # 버튼 2 클릭
        button2 = wait.until(EC.element_to_be_clickable((By.XPATH, '//li[@theater_cd="0013"]')))
        button2.click()

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.day.dimmed')))
        content = driver.page_source

        soup = BeautifulSoup(content, 'html.parser')
        days = soup.find_all(class_='day')
        movies = soup.select('#movie_list .content li a[title]')

        for movie in movies:
            movielist += '\n' + movie['title']

        # 가장 마지막으로 dimmed 클래스가 없는 요소 선택
        for day in reversed(days):
            classes = day.get('class', [])
            if 'dimmed' not in classes and 'date' in day.attrs:
                date = day['date']

                if currentdate != date:
                    currentdate = date
                    await send_msg(f'{date[0:4]}년 {int(date[4:6])}월 {int(date[6:8])}일', movielist)
                    logging.info('Update Detected!')
                else:
                    logging.info('No Update')
                break

    except Exception as e:
        logging.error(f'Error occurred: {e}')
    finally:
        driver.quit()

application = ApplicationBuilder().token(token).build()
job_queue = application.job_queue
job_queue.run_repeating(callback, interval=120)
application.run_polling()
