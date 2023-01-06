import argparse
import logging
import os
from urllib.parse import urljoin
import requests
import json
import scrapy
import toml
import shutil
import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess, install_reactor
from scrapy_playwright.page import PageMethod
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger('scrapy').propagate = False
logging.getLogger('urllib3').propagate = False
logging.getLogger('selenium').propagate = False
logging.getLogger('scrapy-playwright').propagate = False
logging.getLogger('asyncio').propagate = False


load_dotenv()
TOKEN = os.getenv('TOKEN')
BASE_URL = f'https://api.telegram.org/bot{TOKEN}'
OUTPUT_PATH = Path("./data/")
NEW_FILE = Path('new.json')
OLD_FILE = Path('old.json')

IGNORED_KEYWORD = ["stoc epuizat"]


class LinksSpider(scrapy.Spider):
    name = "links"

    def __init__(self, *args, **kwargs):
        super(LinksSpider, self).__init__(*args, **kwargs)
        self.dictionary = kwargs.get('config_dict')

    def start_requests(self):
        options = self.dictionary
        logging.info(datetime.now().strftime(
            "%m/%d/%Y %H:%M:%S") + ": " + options.get('name'))

        if options.get('driver') == 'playwright':
            yield scrapy.Request(url=options.get('link'),
                                 callback=self.parse_wrapper(
                                     product=options.get('name')),
                                 meta=dict(playwright=True,
                                           playwright_page_methods=[
                                               PageMethod(
                                                   "wait_for_timeout", 3000)
                                           ]))
        else:
            yield scrapy.Request(url=options.get('link'), callback=self.parse_wrapper(options.get('name')), meta={"playwright": False})

    def parse_wrapper(self, product):
        def parse(response):
            logging.info(f"response.status:{response.status} - {product}")
            for item in response.xpath(self.dictionary['root']):
                payload = {}
                payload['product'] = product
                for field, path in self.dictionary['fields'].items():
                    if field == 'href':
                        payload['href'] = urljoin(
                            self.dictionary['link'], item.xpath(path).get())
                    else:
                        payload[field] = item.xpath(path).get()
                yield payload
            if self.dictionary.get('next-page') is not None:
                next_page = response.xpath(self.dictionary.get('next-page')).get()
                if next_page is not None:
                    next_page_url = response.urljoin(next_page)
                    options = self.dictionary
                    if options.get('driver') == 'playwright':
                        yield scrapy.Request(url=next_page_url,
                                            callback=self.parse_wrapper(
                                                product=options.get('name')),
                                            meta=dict(playwright=True,
                                                    playwright_page_methods=[
                                                        PageMethod(
                                                            "wait_for_timeout", 3000)
                                                    ]))
                    else:
                        yield scrapy.Request(url=next_page_url, callback=self.parse_wrapper(options.get('name')), meta={"playwright": False})
        return parse


def send_message(message, chat_ids):
    for id in chat_ids:
        send_text = f'{BASE_URL}/sendMessage?chat_id={id}&parse_mode=MarkdownV2&text={message}'
        response = requests.get(send_text)


def craft_message(reason, new_item, old_item=None):
    message = ""
    if reason == 'new':
        message += f'NEW product\n'
    elif reason == 'stoc':
        message += f'STOCK change \nOLD stock: {old_item["stoc"].strip()} \nNEW stock: {new_item["stoc"].strip()}\n'
    elif reason == 'price':
        message += f'PRICE change \nOLD price: {old_item["price"].strip()} \nNEW price: {new_item["price"].strip()}\n'
    elif reason == 'job_listing':
        message += f'NEW job found'
    for _, value in new_item.items():
        message += f'{value.strip()}\n'
    # Escape Markdown reserved characters
    reserved_chars = '''_*[]()~`>+-=|{}.!?'''
    mapper = ['\\' + c for c in reserved_chars]
    result_mapping = str.maketrans(dict(zip(reserved_chars, mapper)))
    message = message.translate(result_mapping)
    message = message.replace('#', '').replace('&', '')
    return message


def start_scraping(config, output_file):
    install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
    process = CrawlerProcess(settings={
        "FEEDS": {
            output_file: {
                "format": "json",
                "overwrite": "True",
            },
        },
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
        "COOKIES_ENABLED": "False",
        "LOG_ENABLED": "False",
        "DOWNLOAD_HANDLERS": {"http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                              "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
                              },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 0,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": '2.7',
    })

    process.crawl(LinksSpider, config_dict=config)
    process.start()


def parse_price(price):
    try:
        return float(price.lower().replace('.', '').replace(' ', '').replace(',', '.').replace('lei', '').replace('ron', '').strip())
    except:
        # Price is none
        return 9999


def check_data(old_file, new_file, chat_ids, config, website):
    if (not old_file.exists()):
        with open(old_file, "w+") as f:
            f.write("[]")

    old = open(old_file, "r+")
    new = open(new_file, "r+")
    old_data = json.load(old)
    try:
        new_data = json.load(new)
        if config['type'] == 'product-listing':
            grouped_old_data = dict()
            grouped_new_data = dict()
            for item in old_data:
                grouped_old_data.setdefault(item['product'], []).append(item)
            for item in new_data:
                grouped_new_data.setdefault(item['product'], []).append(item)

            for product in grouped_new_data:
                if grouped_old_data.get(product) is not None:
                    old_items = {item['href']: {'price': item['price'], 'stoc': item['stoc']}
                                    for item in grouped_old_data[product]}
                else:
                    old_items = {}
                # Check if there are new products by comparing the keys specified in criterias
                for new_item in grouped_new_data[product]:
                    message = None
                    key = new_item['href']
                    stock = new_item.get('stoc').strip().lower()
                    new_price = parse_price(new_item.get('price'))
                    if new_price <= config['price-limit']:
                        if key not in old_items:
                            if stock not in IGNORED_KEYWORD:
                                logging.info("New item - " +
                                                new_item['title'].strip())
                                message = craft_message(
                                    new_item=new_item, reason='new')
                        elif new_item['stoc'] != old_items[key]['stoc']:
                            logging.info("New stock update " + key.strip())
                            message = craft_message(
                                reason='stoc', new_item=new_item, old_item=old_items[key])
                        else:
                            old_price = parse_price(
                                old_items[key]['price'])
                            if abs(old_price - new_price) > config['threshold']:
                                logging.info(
                                    f"New price for {new_item['title'].strip()} - OLD: {old_price}, NEW: {new_price}")
                                message = craft_message(
                                    reason='price', new_item=new_item, old_item=old_items[key])
                    if message != None:
                        send_message(message, chat_ids)
        elif config['type'] == 'job-listing':
            for listing in new_data:
                position = listing.get('position').lower()
                for word in config['keywords']:
                    if word in position and listing not in old_data:
                        logging.info("New position - " +
                                        listing['position'].strip())
                        message = craft_message(reason='new_job_listing', new_item=listing)
                        send_message(message, chat_ids)
        shutil.copy2(new_file, old_file)
    except Exception as e:
        new_data = [] 
        send_message(
            f"ERROR: Couldn't scrape items from {website}\\!", chat_ids)
        logging.error(
            f"{datetime.now().strftime('%m/%d/%Y %H:%M:%S')}: ERROR: Couldn't scrape items from {website}!")
        logging.exception(e)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_path", required=True,
                        help="Path to the config.yaml file")
    parser.add_argument("-e", "--env_chat_ids", required=True, action='store', nargs='+',
                        help="Variables from env file containing the Chat IDs")
    parser.add_argument("-s", "--subscribers",
                        help="Path to subscribers.toml file")
    args = parser.parse_args()

    config_path = Path(args.config_path)
    old_file = OUTPUT_PATH / config_path.stem / OLD_FILE
    output_file = OUTPUT_PATH / config_path.stem / NEW_FILE

    if not config_path.exists():
        logging.error("Config not found, exiting...")
        exit()

    chat_ids = []
    for name in args.env_chat_ids:
        id = os.getenv(name)
        if id == None:
            logging.error(f"ID for {name} not found, exiting...")
            exit()
        chat_ids.append(id)

    config = toml.load(args.config_path)
    # start_scraping(config, output_file)
    check_data(old_file, output_file, chat_ids, config, config_path.stem)


if __name__ == "__main__":
    main()
