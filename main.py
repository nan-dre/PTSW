import os
import shutil
import requests
import json
import scrapy
import yaml
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
url = "https://api.telegram.org/bot" + TOKEN
OUTPUT_PATH = Path("./data/")
class LinksSpider(scrapy.Spider):
    name = "links"

    def __init__(self, *args, **kwargs):
        super(LinksSpider, self).__init__(*args, **kwargs)
        with open("config.yaml", 'r') as f:
            self.dictionary = yaml.safe_load(f)

    def start_requests(self):
        for site, key in self.dictionary.items():
            self.cur_site = site
            print(datetime.now().strftime("%m/%d/%Y %H:%M:%S") + ": " + site)
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
    # Escape Markdown reserved characters
    reserved_chars = '''_*[]()~`>#+-=|{}.!'''
    mapper = ['\\' + c for c in reserved_chars]
    result_mapping = str.maketrans(dict(zip(reserved_chars, mapper)))
    message = message.translate(result_mapping)

    # Create the link and make the get request
    send_text = url + "/sendMessage" + "?chat_id=" + \
        CHAT_ID + "&parse_mode=MarkdownV2&text=" + message
    response = requests.get(send_text)
    print(item['title'])
    return response.json()


def main():
    # Scraping
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
                send(new_el)
    shutil.copy2("./data/items.json", "./data/items_old.json")


if __name__ == "__main__":
    main()
