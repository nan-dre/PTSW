import scrapy
from scrapy.crawler import CrawlerProcess

from time import sleep
import os
import shutil
import requests
import json
from dotenv import load_dotenv
from pprint import pprint
import yaml

load_dotenv()
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
url = "https://api.telegram.org/bot" + TOKEN
OUTPUT_PATH="./data/"
OUTPUT_FILE="items.json"

class LinksSpider(scrapy.Spider):
    name = "links"

    def __init__(self, *args, **kwargs):
        super(LinksSpider, self).__init__(*args, **kwargs)
        with open("config.yaml", 'r') as f:
            self.dictionary = yaml.load(f)

    def start_requests(self):
        for site, key in self.dictionary.items():
            self.cur_site = site
            print(site)
            yield scrapy.Request(url=key['link'], callback=self.parse)

    def parse(self, response):
        for item in response.xpath(self.dictionary[self.cur_site]['root']):
            yield {
                'href': item.xpath(self.dictionary[self.cur_site]['href']).get(),
                'title': item.xpath(self.dictionary[self.cur_site]['title']).get(),
                'place': item.xpath(self.dictionary[self.cur_site]['place']).get(),
                'date': item.xpath(self.dictionary[self.cur_site]['date']).get(),
                'price': item.xpath(self.dictionary[self.cur_site]['price']).get(),
            }

def send(item):
    message = (
        f"{item['title']}\n"
        f"{item['price']}\n"
        f"{item['place']} - "
        f"{item['date']}\n"
        f"{item['href']}"

    )
    send_text = url + "/sendMessage" + "?chat_id=" + CHAT_ID + "&parse_mode=Markdown&text=" + message
    response = requests.get(send_text)
    print("Sending message...")
    return response.json()

if __name__ == "__main__":
    #Scraping
    process = CrawlerProcess(settings={
        "FEEDS": {
            "data/items.json": {
                "format": "json",
                "overwrite": "True",
            },
        },
        "USER_AGENT": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0",
        "COOKIES_ENABLED": "False",
        "LOG_ENABLED": "False",

    })

    process.crawl(LinksSpider)
    process.start()

    # Updating the data files and sending to telegram
    if os.path.exists("./data/items_old.json"):
        old = open("./data/items_old.json", "r+")
        new = open("./data/items.json", "r+")
        old_data=json.load(old)
        new_data=json.load(new)
        for i in new_data:
            if i not in old_data:
                send(i)
    shutil.copy2("./data/items.json", "./data/items_old.json")
