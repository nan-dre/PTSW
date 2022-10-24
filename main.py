import argparse
import logging
import os
from urllib.parse import urljoin
import requests
import json
import scrapy
import yaml
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
        with open(kwargs.get('config_path'), 'r') as f:
            self.dictionary = yaml.safe_load(f)

    def start_requests(self):
        for site, key in self.dictionary.items():
            self.cur_site = site
            logging.info(datetime.now().strftime("%m/%d/%Y %H:%M:%S") + ": " + site)
            yield scrapy.Request(url=key['link'], callback=self.parse)

    def parse(self, response):
        logging.info(f"response.status:{response.status}")
        for item in response.xpath(self.dictionary[self.cur_site]['root']):
            payload = {}
            for field, path in self.dictionary[self.cur_site]['fields'].items():
                if field == 'relative-href':
                    payload['href'] = urljoin(self.dictionary[self.cur_site]['link'], item.xpath(path).get())
                else:
                    payload[field] = item.xpath(path).get()
            yield payload


def send(item, chat_id):
    message = ""
    for field, value in item.items():
        message += f'{value.strip()}\n'
    # Escape Markdown reserved characters
    reserved_chars = '''_*[]()~`>+-=|{}.!?'''
    mapper = ['\\' + c for c in reserved_chars]
    result_mapping = str.maketrans(dict(zip(reserved_chars, mapper)))
    message = message.translate(result_mapping)
    message = message.replace('#', '')

    # Create the link and make the get request
    send_text = f'{BASE_URL}/sendMessage?chat_id={chat_id}&parse_mode=MarkdownV2&text={message}'
    response = requests.get(send_text)
    logging.info(item['title'])
    return response.json()


def start_scraping(config_path):
    process = CrawlerProcess(settings={
        "FEEDS": {
            OUTPUT_PATH / config_path.stem / NEW_FILE: {
                "format": "json",
                "overwrite": "True",
            },
        },
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64; rv:105.0) Gecko/20100101 Firefox/105.0",
        "COOKIES_ENABLED": "False",
        "LOG_ENABLED": "False",
    })

    process.crawl(LinksSpider, config_path=config_path)
    process.start()


def check_data(old_file, new_file, chat_id):
    if os.path.exists(old_file):
        old = open(old_file, "r+")
        new = open(new_file, "r+")
        old_data = json.load(old)
        new_data = json.load(new)
        criterias = ['price', 'title']
        # Check if there are new products by comparing the keys specified in criterias
        # Pretty sure there's a more "pythonic" way to do this that I don't see
        for new_el in new_data:
            found = False
            for old_el in old_data:
                crit_found = 0
                for crit in criterias:
                    if new_el[crit] == old_el[crit]:
                        crit_found += 1
                if crit_found == len(criterias):
                    found = True
            if not found:
                send(new_el, chat_id)
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
    old_file = OUTPUT_PATH / Path(args.config_path).stem / OLD_FILE
    new_file = OUTPUT_PATH / Path(args.config_path).stem / NEW_FILE

    if chat_id == None:
        logging.error("Chat ID not found, exiting...")
        exit()
    if not config_path.exists():
        logging.error("Config not found, exiting...")
        exit()


    start_scraping(config_path)
    check_data(old_file, new_file, chat_id)


if __name__ == "__main__":
    main()
