# PTSW
##### *python telegram scraper watcher (who comes-up with these names? Oh, I do)*

A python script that scrapes e-commerce websites for new products and sends updates about them through Telegram.

PTSW has the ability to scrape multiple websites and update the xpath selectors for each of them, with a config.toml file. See below.

## But why, why another webscraper?
I needed a scraper that was specific enough for the need of finding new items on e-commerce sites, yet general enough so that I can scrape multiple sites with it.

## Installation
Make sure you have Python 3 installed. I recommend [Miniconda]( https://docs.conda.io/en/latest/miniconda.html ), I find it easier to manage your environments.

```
pip3 install -r requirements.txt
```

## Using PTSW
You will need to create 2 files:
* A .env file, in the root of the repo, containing
```
TOKEN='<your-telegram-bot-token>'
CHAT_ID='<your-telegram-account-chat-id>'
```
[ Here's ](https://core.telegram.org/bots#6-botfather) a guide on creating telegram bots and [here's](https://stackoverflow.com/questions/32423837/telegram-bot-how-to-get-a-group-chat-id) a guide showing how to find your chat id.

* A config.toml file, with the following structure
```toml
[site]
link = '<website>'
root = '//div[@class="css-1apmciz"]'
threshold = 10
price-limit = 2200

[olx.fields]
title = 'div/h6/text()'
price = 'div[1]/p/text()'
stoc = 'div[2]/p/text()[1]'
date = 'div[2]/p/text()[3]'
relative-href = '../../../../a/@href'
```
The root-xpath needs to be a common xpath for all the other fields (something like an item container). We can place any number of xpaths in the fields dict.
The title and price fields are mandatory, in order to check for new products or new price updates. The `relative-href` field is used in order to correctly send the link
to the product via telegram (some products show the href in the html source relative to the current address, so we just concatenate the relative-href to the link field in order to get the full address).

We receive updates only when there are new products listed and their price is lower than the `price-limit`, or when a product updates its price and the difference between the old price and the new price is greater than the `threshold`.


I used the browser developer console and scrapy shell in order to find the correct xpaths for each website. [Here](https://docs.scrapy.org/en/latest/topics/selectors.html) is more information on scrapy and selectors. It's a _painstaking_ process to get the exact xpaths for each field, but this is the strong suit of the project: to be able to iterate quickly on multiple sites.


Running the script will create a `new.json` file in the **data/<config_file_stem>** folder and a `old.json` file, which contains a copy of new.json. The `old.json` file contains the items scraped on latest run, and the `new.json` file contains items scraped on current run. The app will compare these to files to check if new products have appeared on the site. If that happens, it will send a telegram message with the new products.

I suggest setting up a cron job that runs this script periodically. Here's an example that runs it every 15 minutes and logs the output to log.txt:

```
*/15 * * * * cd ~/projects/PTSW/ && python3 main.py -c <config_file> -e <env_chat_id> >> log.txt
```

Beware that some sites might [ban your ip](https://docs.scrapy.org/en/latest/topics/practices.html#avoiding-getting-banned) if there is too much traffic.

## Docker

I also wrote a Dockerfile for it, run it with

```
docker build -t ptsw .
docker run -d ptsw
```

## Dependencies
Some python3 libraries:
* scrapy
* requests
* python-dotenv
* toml


