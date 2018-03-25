# basic telegram bot
# https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay
# https://github.com/sixhobbits/python-telegram-tutorial/blob/master/part1/echobot.py

import json 
import requests
import time
import urllib
import config
import urllib.parse
from lxml import objectify
# python3: urllib.parse.quote_plus
# python2: urllib.pathname2url
TOKEN = config.TOKEN
#TOKEN = "<your-bot-token>" # don't put this in your repo! (put in config, then import config)
URL = "https://api.telegram.org/bot{}/".format(TOKEN)


def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None, timeout=100):
    url = URL + "getUpdates?timeout={}".format(timeout)
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def get_last_chat_id_and_text(updates):
    print(len(updates["result"]))
    last_update = - 1
    try:
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    except IndexError:
        return (None, None)
    except Exception as e:
        print(e)
        return (None, None)
    return (text, chat_id)


def send_message(text, chat_id):
    text = urllib.parse.quote_plus(text) # urllib.parse.quote_plus(text) # (python3)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    get_url(url)


def echo_all(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            send_message(text, chat)
        except Exception as e:
            print(e)


def main():
    last_textchat = (None, None)
    last_update_id = None
    auth = (config.NS_UN, config.NS_WW)
    print("testing NS")
    print(objectify.parse(requests.get("http://webservices.ns.nl/ns-api-avt?station=utrecht", auth=auth).content))
    print("done testing")
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            if updates["result"][-1]["message"]["text"] == "The secret testing string.":
                print(get_json_from_url(URL+"Sendmessage?text=bla+bla&reply_markup=keyboard?KeyboardButton?text=gib+location&request_location=true"))
            else:
                echo_all(updates)
            last_update_id = get_last_update_id(updates)+1
            print([update["update_id"] for update in updates["result"]])
        time.sleep(0.5)


if __name__ == '__main__':
    main()
