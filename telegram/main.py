from time import sleep
import os
import shutil
import requests
import json
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()
TOKEN = os.getenv('TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
url = "https://api.telegram.org/bot" + TOKEN

def send(item):
    message = (
        f"{item['title']}\n"
        f"{item['place']} - "
        f"{item['date']}\n"
        f"{item['price']}\n"
        f"{item['link']}"

    )
    send_text = url + "/sendMessage" + "?chat_id=" + CHAT_ID + "&parse_mode=Markdown&text=" + message
    response = requests.get(send_text)
    print("Sending message...")
    return response.json()



if __name__ == "__main__":
    print("Script is running...")
    old = open("../data/olx_old.json", "r+")
    new = open("../data/olx.json", "r+")
    old_data=json.load(old)
    new_data=json.load(new)
    for i in new_data:
        if i not in old_data:
            send(i)
    shutil.copy2("../data/olx.json", "../data/olx_old.json")

