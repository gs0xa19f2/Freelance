import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('.json', scope)
client = gspread.authorize(creds)
spreadsheet_id = '' 
sheet = client.open_by_key(spreadsheet_id).sheet1

sheet.append_row(['Название компании', 'Оценка', 'Отзыв'])
logging.info("Заголовки для отзывов добавлены.")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7'
}

def setup_selenium():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  
    options.add_argument('--no-sandbox')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

def load_page_with_selenium(url, driver):
    try:
        driver.get(url)
        while True:
            try:

                show_more_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Показать ещё отзывы')]"))
                )
                driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(2)  
            except:
                break  
        return driver.page_source
    except Exception as e:
        logging.error(f"Ошибка при загрузке страницы с отзывами: {e}")
        return None


def get_rating(container):

    stars = container.find_all('svg', {'class': 'Icon-svg-Nue9W'})
    rating = 0
    for star in stars:

        fill_color = star.find('path')['fill']
        if fill_color == '#ffb021': 
            rating += 1
        elif fill_color == '#e3e2e1': 
            continue
    return rating

def parse_reviews(company_name, company_url, driver):
    logging.info(f"Запрос отзывов для компании: {company_name} по URL: {company_url}")
    
    page_html = load_page_with_selenium(company_url, driver)
    if not page_html:
        logging.error(f"Не удалось загрузить страницу: {company_url}")
        return []

    soup = BeautifulSoup(page_html, 'html.parser')


    review_containers = soup.find_all('div', class_=re.compile(r'ReviewSnippet-root'))

    if not review_containers:
        logging.error(f"Отзывы не найдены на странице {company_url}")
        return []

    parsed_reviews = []
    unique_reviews = set()  

    for container in review_containers:
        review_text_container = container.find('div', class_='Cut-cut-cOXuU')
        review_text = review_text_container.text.strip() if review_text_container else 'Нет отзыва'
        
        review_rating = get_rating(container)

        if review_text not in unique_reviews:
            parsed_reviews.append([company_name, review_rating if review_rating else 'Без оценки', review_text])
            unique_reviews.add(review_text)

    logging.info(f"Найдено уникальных отзывов: {len(parsed_reviews)}")
    return parsed_reviews

companies = [
    {"name": "АЛЬМАК ПРОКАТ", "url": "https://www.avito.ru/brands/almak_prokat/all/predlozheniya_uslug?sellerId=f5121746422bff79628333a693e3771c"},
    {"name": "LocalCar", "url": "https://www.avito.ru/brands/6d9790d5aedc2465c513feefde37086b/all/predlozheniya_uslug?sellerId=4ae4e7b89221fe0d193518f469993eb6"},
    {"name": "CARS-GO", "url": "https://www.avito.ru/brands/i269866186/all/predlozheniya_uslug?sellerId=5ca94d7c7f7eead225cb37046c01b4c9"},
    {"name": "LEO CARS", "url": "https://www.avito.ru/brands/leocars.ru/all?sellerId=e9d6726d02c73de9080a5a7ab8637041"},
    {"name": "Vroom.club", "url": "https://www.avito.ru/brands/i199578510/all/predlozheniya_uslug?sellerId=9e3568bc7baf59a368843b92804dc255"},
    {"name": "Авто прокат сервис", "url": "https://www.avito.ru/brands/autoprokat-service/all?sellerId=50d2c06d702c28d69d9d2793b8fc2a9d"},
    {"name": "MoscowDreamCars", "url": "https://www.avito.ru/brands/i5174950/all/predlozheniya_uslug?sellerId=bf3de3a953593104f8c773c959f9c06bb"},
    {"name": "WHEELZ MOSCOW", "url": "https://www.avito.ru/brands/wheelzmoscow/all?sellerId=b9e3d1287adee264115e3250de017d57"},
    {"name": "Premier Cars", "url": "https://www.avito.ru/brands/i203723948/all/predlozheniya_uslug?sellerId=0aebc0ee5bf2b994c09b764c2e395824"},
    {"name": "Ricci Car", "url": "https://www.avito.ru/brands/i320099662/all/predlozheniya_uslug?sellerId=33cd82d4b7b1efab377a4ea0745cbdda"},
    {"name": "Wheels4Rent", "url": "https://www.avito.ru/brands/wheels4rent/all/predlozheniya_uslug?sellerId=76da5a65fa4a5b286fc0deb9e9035daf"},
    {"name": "ОЛФОЮ КАРС", "url": "https://www.avito.ru/brands/i59190191/all/predlozheniya_uslug?sellerId=2daa02af5b12019443912e1d998f7de2"},
    {"name": "Capital Drive", "url": "https://www.avito.ru/brands/capitaldrive/all?sellerId=a817e7f57357d4a3ffe608ff39ef0a14"},
    {"name": "Би Карс", "url": "https://www.avito.ru/brands/bee-cars/all?sellerId=fccd94b53d75d63abd2a5bf80ad45509"},
    {"name": "PREMIUMCAR", "url": "https://www.avito.ru/brands/i181028021/all/predlozheniya_uslug?sellerId=ee9eb2a247719241bdf114a841171359"},
    {"name": "AVTO-E", "url": "https://www.avito.ru/brands/i13850157/all?p=sellerId=0a5853d35e2cf007cc545e7bc264b8e9"},
    {"name": "Carloson Club", "url": "https://www.avito.ru/brands/carloson/all/predlozheniya_uslug?sellerId=714a3f71b71d0bd05bb1537858cd66b4"},
    {"name": "G-AUTO", "url": "https://www.avito.ru/brands/i371005813/all?p=sellerId=0f1522ce8af8dbd77198b2e1f24bdf8f"},
    {"name": "KREMLINCARS MOSCOW", "url": "https://www.avito.ru/brands/kremlin_cars_moscow77/all?p=sellerId=9f630194ce9a9bff01a6a2408730c52f"},
    {"name": "FIRST AUTO CLUB", "url": "https://www.avito.ru/brands/cde8fb1d5936807dab27cb9a3473aba3/all?p=sellerId=b0ea84dccd75742130678584e8fcc113"},
    {"name": "Автопрокат Карета", "url": "https://www.avito.ru/brands/e89757b6d688df4d16abeb89377fc589/all?p=sellerId=e911b2110e6c7262c194a61b3744393c"},
    {"name": "Best Auto", "url": "https://www.avito.ru/brands/i294198466/all?p=sellerId=b5e938580d5fb4b2820f4cc9af99b96e"},
    {"name": "FrankRent", "url": "https://www.avito.ru/brands/i373114438/all?p=sellerId=0938b28e0c5c21be52abfec555209ea1"},
    {"name": "Рента-Востокавто", "url": "https://www.avito.ru/brands/renta-vostokauto/all?p=sellerId=e44ce8ddeae6d9a86326a3ba8873faf9"},
    {"name": "АвтоАренда 365", "url": "https://www.avito.ru/brands/i94924452/all?p=sellerId=4181c54854a867ab498af03bdbbc8550"},
    {"name": "ArusRent", "url": "https://www.avito.ru/brands/i304325522/all?p=sellerId=caef586aa943cbf822fefd8cb98821ec"},
    {"name": "АА - Аренда Авто", "url": "https://www.avito.ru/brands/a1ef467b34966b16c6cfaec5fe65ebe9/all?p=sellerId=a1ef467b34966b16c6cfaec5fe65ebe9"},
    {"name": "ПлюсАвто", "url": "https://www.avito.ru/brands/i360472993/all?p=sellerId=88b3acc7005675ecb1bb78abe9cc151c"},
    {"name": "Прокат кабриолетов и премиум авто", "url": "https://www.avito.ru/brands/cabrio/all?p=sellerId=3ff2a00b4bdb3f71e839f3a41a6bdd25"},
    {"name": "Прокатное Бюро МЕРИН", "url": "https://www.avito.ru/brands/i213240870/all?p=sellerId=140616ba3f0e93eaf926bd79d2868aee"},
    {"name": "КОМФОРТНЫЙ АВТОПРОКАТ", "url": "https://www.avito.ru/brands/i370969568"},
    {"name": "AUTOPILOT", "url": "https://www.avito.ru/brands/i125913199"},
    {"name": "Паритет", "url": "https://www.avito.ru/user/cb3ffc3823c744b8b15f1869a62e3fd6/profile"},
    {"name": "Premium Rental Car", "url": "https://www.avito.ru/brands/premiumrentalcar/all?p=sellerId=a2ece64b9b7839d8cd0aed9e525fd938"},
]


# Переменная для накопления всех отзывов
all_reviews = []

# Запуск Selenium
driver = setup_selenium()

# Парсинг отзывов для всех компаний
for company in companies:
    reviews = parse_reviews(company['name'], company['url'], driver)
    all_reviews.extend(reviews)
    # Задержка между запросами для снижения вероятности блокировки
    time.sleep(random.randint(20, 60))

# Закрываем браузер
driver.quit()

# Добавляем все отзывы в таблицу одной командой
if all_reviews:
    sheet.append_rows(all_reviews)
    logging.info(f"Добавлено {len(all_reviews)} уникальных отзывов.")

logging.info("Парсинг завершен.")

