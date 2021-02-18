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

class LinksSpider(scrapy.Spider):
    name = "links"
    def __init__(self):
        with open("config.yaml", 'r') as f:
            self.dictionary = yaml.load(f)

    def parse(self, response):
        for item in response.xpath('//div[@class="offer-wrapper"]/table/tbody'):
            yield {
                'link': item.xpath('tr/td/div/h3/a/@href').get(),
                'title': item.xpath('tr/td/div/h3/a/strong/text()').get(),
                'place': item.xpath('tr/td/div/p/small/span/text()').getall()[0],
                'date': item.xpath('tr/td/div/p/small/span/text()').getall()[1],
                'price': item.xpath('tr/td/div/p/strong/text()').get(),
            }

def send(item):
    message = (
        f"{item['title']}\n"
        f"{item['price']}\n"
        f"{item['place']} - "
        f"{item['date']}\n"
        f"{item['link']}"

    )
    send_text = url + "/sendMessage" + "?chat_id=" + CHAT_ID + "&parse_mode=Markdown&text=" + message
    response = requests.get(send_text)
    print("Sending message...")
    return response.json()

if __name__ == "__main__":
    #Scraping
    process = CrawlerProcess(settings={
        "FEEDS": {
            "data/olx.json": {"format": "json"},
        },
        "USER_AGENT": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0",
        "COOKIES_ENABLED" : "False"
    })

    process.crawl(LinksSpider)
    process.start()

    # Updating the data files and sending to telegram
    old = open("./data/olx_old.json", "r+")
    new = open("./data/olx.json", "r+")
    old_data=json.load(old)
    new_data=json.load(new)
    for i in new_data:
        if i not in old_data:
            send(i)
    shutil.copy2("./data/olx.json", "./data/olx_old.json")
