# PTSW
##### *python telegram scraper watcher (who comes-up with these names? Oh, I do)*

A python script that scrapes e-commerce websites for new products and sends you informations about them through Telegram.

PTSW has the ability to scrape multiple websites and update the xpath selectors for each of them, with a config.yaml file. See below.

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
[ Here's ](https://core.telegram.org/bots#6-botfather) a guide on creating telegram bots and [here's](https://www.wikihow.com/Know-Chat-ID-on-Telegram-on-Android) a guide showing how to find your chat id.

* A config.yaml file, with the following structure
```
website_name:
  link: '<website_link>'
  root: '<root-xpath>'
  href: '<href-xpath>'
  title: '<title-xpath>'
  place: '<place-xpath>'
  date:  '<date-xpath>'
  price: '<price-xpath>'
```
The root-xpath needs to be a common xpath for all other fields (something like an item container). In case you don't need a field, just put '/..' in it's place. 

There is an example config.yaml in the repo.

I used scrapy shell in order to find the correct xpaths for each website. [Here](https://docs.scrapy.org/en/latest/topics/selectors.html) is more information on scrapy and selectors.

After creating these files, you can run the script:
```
python main.py
```

On it's first run it will create a items.json file in the **data** folder and a items_old.json, which contains a copy of items.json. On latter runs, it will compare items.json with items_old.json to check if new products have appeared on the site. If that happens, it will send you a telegram message with the new products.

I suggest setting up a cron job that runs this script periodically. Here's an example that runs it every 15 minutes and logs the output to log.txt:

```
*/15 * * * * cd ~/projects/PTSW/ && python3 main.py >> log.txt
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
* pyyaml


