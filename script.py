import scrapy
from scrapy.crawler import CrawlerProcess

class LinksSpider(scrapy.Spider):
    name = "links"
    start_urls = [
        'https://www.olx.ro/bucuresti-ilfov-judet/q-tastatura-razer/'
    ]

    def parse(self, response):
        for item in response.xpath('//div[@class="offer-wrapper"]/table/tbody'):
            yield {
                'link': item.xpath('tr/td/div/h3/a/@href').get(),
                'title': item.xpath('tr/td/div/h3/a/strong/text()').get(),
                'place': item.xpath('tr/td/div/p/small/span/text()').getall()[0],
                'date': item.xpath('tr/td/div/p/small/span/text()').getall()[1],
                'price': item.xpath('tr/td/div/p/strong/text()').get(),
            }

process = CrawlerProcess(settings={
    "FEEDS": {
        "data/olx.json": {"format": "json"},
    },
    "USER_AGENT": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0",
    "COOKIES_ENABLED" : "False"
})

process.crawl(LinksSpider)
process.start() # the script will block here until the crawling is finished
