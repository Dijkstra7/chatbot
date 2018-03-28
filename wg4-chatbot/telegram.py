# basic telegram bot
# https://www.codementor.io/garethdwyer/building-a-telegram-bot-using-python-part-1-goi5fncay
# https://github.com/sixhobbits/python-telegram-tutorial/blob/master/part1/echobot.py

import json
import requests
import time
import urllib
import config
import urllib.parse
# from lxml import objectify
from bot_speech import BotCommunication
from NS_connect import NS_info

# python3: urllib.parse.quote_plus
# python2: urllib.pathname2url
TOKEN = config.TOKEN
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
		return None, None
	except Exception as e:
		print(e)
		return None, None
	return text, chat_id


def make_keyboard(buttons):
	keyboard = [[button] for button in buttons]
	keyboard_code = {'inline_keyboard': keyboard}
	return json.dumps(keyboard_code)


def send_message(text, chat_id, buttons):
	text = urllib.parse.quote_plus(
		text)  # urllib.parse.quote_plus(text) # (python3)
	url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
	if buttons is not None:
		url += "&reply_markup={}".format(make_keyboard(buttons))
	get_url(url)


def echo_all(updates):
	for update in updates["result"]:
		try:
			text = update["message"]["text"]
			chat = update["message"]["chat"]["id"]
			send_message(text, chat)
		except Exception as e:
			print(e)


def send_messages(messages, keyboard_buttons=None):
	for button_id, text, chat_id in enumerate(messages):
		if keyboard_buttons is not None:
			send_message(text, chat_id)
		else:
			send_message(text, chat_id, keyboard_buttons[button_id])


def main():
	ns_info = NS_info()
	communicator = BotCommunication(ns_info)
	last_update_id = None
	print("Bot has started")
	while True:
		updates = get_updates(last_update_id)
		if len(updates["result"]) > 0:
			print(updates["result"])
			communicator.receive_message(updates)
			while communicator.response_waiting is True:
				response = communicator.respond()
				send_message(*response)
				print("sending message: {}".format(response))
			last_update_id = get_last_update_id(updates) + 1
			# print([update["update_id"] for update in updates["result"]])
		time.sleep(0.5)


if __name__ == '__main__':
	main()
