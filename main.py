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
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger('scrapy').propagate = False
logging.getLogger('urllib3').propagate = False


load_dotenv()
TOKEN = os.getenv('TOKEN')
BASE_URL = f'https://api.telegram.org/bot{TOKEN}'
OUTPUT_PATH = Path("./data/")
NEW_FILE = Path('new.json')
OLD_FILE = Path('old.json')


class LinksSpider(scrapy.Spider):
    name = "links"

    def __init__(self, *args, **kwargs):
        super(LinksSpider, self).__init__(*args, **kwargs)
        self.dictionary = kwargs.get('config_dict')

    def start_requests(self):
        for product, value in self.dictionary.items():
            logging.info(datetime.now().strftime("%m/%d/%Y %H:%M:%S") + ": " + product)
            yield scrapy.Request(url=value['link'], callback=self.parse_wrapper(product))

    def parse_wrapper(self, product):
        def parse(response):
            logging.info(f"response.status:{response.status} - {product}")
            for item in response.xpath(self.dictionary[product]['root']):
                payload = {}
                payload['product'] = product
                for field, path in self.dictionary[product]['fields'].items():
                    if field == 'relative-href':
                        payload['href'] = urljoin(self.dictionary[product]['link'], item.xpath(path).get())
                    else:
                        payload[field] = item.xpath(path).get()
                yield payload
        return parse


def send(item, chat_id, old_price=None, new_price=None):
    message = ""
    for field, value in item.items():
        message += f'{value.strip()}\n'
    # Escape Markdown reserved characters
    reserved_chars = '''_*[]()~`>+-=|{}.!?'''
    mapper = ['\\' + c for c in reserved_chars]
    result_mapping = str.maketrans(dict(zip(reserved_chars, mapper)))
    message = message.translate(result_mapping)
    message = message.replace('#', '')

    if new_price:
        message += f'OLD price: {old_price}, NEW price: {new_price}\n'

    # Create the link and make the get request
    send_text = f'{BASE_URL}/sendMessage?chat_id={chat_id}&parse_mode=MarkdownV2&text={message}'
    response = requests.get(send_text)
    logging.info(item['title'])
    return response.json()


def start_scraping(config, output_file):
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
    })

    process.crawl(LinksSpider, config_dict=config)
    process.start()

def check_data(old_file, new_file, chat_id, config):
    if os.path.exists(old_file):
        old = open(old_file, "r+")
        new = open(new_file, "r+")
        old_data = json.load(old)
        new_data = json.load(new)

        grouped_old_data = dict()
        grouped_new_data = dict()
        for item in old_data:
            grouped_old_data.setdefault(item['product'], []).append(item)
        for item in new_data:
            grouped_new_data.setdefault(item['product'], []).append(item)

        for product in grouped_new_data:
            pairs = {item['title']: item['price'] for item in grouped_old_data[product]}
            # Check if there are new products by comparing the keys specified in criterias
            for new_item in grouped_new_data[product]:
                new_price = int(new_item['price'].replace('.', ''))
                if new_item['title'] not in pairs:
                    if new_price <= config[product]['price-limit']:
                        logging.info("New item - " + new_item['title'])
                        send(new_item, chat_id)
                else:
                    old_price = int(pairs[new_item['title']].replace('.', ''))
                    if (old_price - new_price) > config[product]['threshold']:
                        logging.info(f"New price for {new_item['title']} - OLD: {old_price}, NEW: {new_price}")
                        send(new_item, chat_id, old_price, new_price)
    shutil.copy2(new_file, old_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_path", required=True,
                        help="Path to the config.yaml file")
    parser.add_argument("-e", "--env_chat_id", required=True,
                        help="Variable from env file containing the Chat ID")
    args = parser.parse_args()

    chat_id = os.getenv(args.env_chat_id)
    config_path = Path(args.config_path)
    old_file = OUTPUT_PATH / config_path.stem / OLD_FILE
    output_file = OUTPUT_PATH / config_path.stem / NEW_FILE 

    if chat_id == None:
        logging.error("Chat ID not found, exiting...")
        exit()
    if not config_path.exists():
        logging.error("Config not found, exiting...")
        exit()

    config = toml.load(args.config_path)

    # start_scraping(config, output_file)
    check_data(old_file, output_file, chat_id, config)


if __name__ == "__main__":
    main()
