import scrapy


class LinksSpider(scrapy.Spider):
    name = "olx"
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
