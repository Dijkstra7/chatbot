import string
# import nltk
import numpy as np


class BotCommunication:
	""" A bot that is reacting to certain messages. """

	def __init__(self, ns_api, history=None):
		self.ns_api = ns_api
		self.messages = []
		self.chat_ids = []
		self.send_this = []
		self.history = history
		if history is None:
			self.history = []
		self.response_waiting = False
		# initialise response generators
		self.did_not_get = NotUnderstoodMessage()
		self.repeater = RepeatAfterMe()
		self.specials = SpecialResponses()
		self.understander = UnderstandResponse(self.ns_api)
		self.planner = TravelPlanner(self)

	def receive_message(self, messages):
		for message in messages["result"]:
			try:
				text = None
				chat_id = None
				if "message" in message:
					text = message["message"]["text"]
					chat_id = message["message"]["chat"]["id"]
				elif "callback_query" in message:
					text = message["callback_query"]["data"]
					chat_id = message["callback_query"]["from"]["id"]
				self.messages.append(text)
				self.chat_ids.append(chat_id)
			except Exception as e:
				print(repr(e))
			self.create_response()

	def create_response(self, ):
		""" Creates a response to the message

		"""
		buttons = None
		last_message = self.messages[-1]
		last_id = self.chat_ids[-1]
		if last_message in self.specials.special_cases:
			reply = self.specials.generate_message(last_message)
		else:
			if self.planner.is_planning is True:
				reply = self.planner.generate_message(last_message)
			else:
				reply = self.understander.generate_message(last_message)
				if self.understander.new_planning is True:
					reply = self.planner.generate_message(last_message, start=True)
					self.understander.new_planning = False
			if reply is None:
				reply = self.did_not_get.generate_message()

		# unpack response
		response = reply["response"]
		if "buttons" in reply:
			buttons = reply["buttons"]
		print(reply)
		self.update_response(response, last_id, buttons)

	def update_response(self, message, chat_id, buttons):
		self.send_this.append((message, chat_id, buttons))
		self.response_waiting = True

	def respond(self):
		if self.response_waiting is True:
			response = self.send_this.pop(0)
			if len(self.send_this) == 0:
				self.response_waiting = False
			self.history.append(response)
			return response
		return None


# Different functions on the messages.
class Responder:
	def __init__(self, *args, **kwargs):
		self.log = []
		pass

	def generate_message(self, *args, **kwargs):
		return None

	def return_message(self, message):
		self.log.append(message)
		return message


class RepeatAfterMe(Responder):
	def __init__(self):
		super(RepeatAfterMe, self).__init__()
		pass

	def generate_message(self, message):
		return self.return_message({"response": message})


class SpecialResponses(Responder):
	def __init__(self):
		super(SpecialResponses, self).__init__()
		self.special_cases = ["/help", "/start"]
		self.special_functions = [self.help, self.start]

	def generate_message(self, message):
		if message not in self.special_cases:
			return self.return_message(None)
		response = self.special_functions[self.special_cases.index(message)]()
		return self.return_message({"response": response})

	def help(self):
		return_string = "I am the NS chatbot. \n" \
								    "I can help you to plan trips that use the train " \
								    "in the Netherlands. \n" \
								    "\n" \
								    "You can ask me questions like:\n" \
								    "- Can you help me plan my trip? \n" \
								    "- How do I get in Amsterdam?\n" \
								    "- What time do I need to leave to arrive in Utrecht at " \
								    "21:00?\n" \
								    "\n" \
								    "And I will generate an advise for you. \n" \
								    "The good part: Since I am using the website of the NS " \
								    "(the Dutch railway company), my information is as up to "\
								    " date as " \
								    "possible."
		return self.return_message(return_string)

	def start(self):
		return_string = " Hello, Nice to see you!\n" \
		                "I am the NS chatbot. \n" \
		                "I can help you to plan trips that use the train " \
		                "in the Netherlands. \n" \
		                "\n" \
		                "You can ask me questions like:\n" \
		                "- Can you help me plan my trip? \n" \
		                "- How do I get in Amsterdam?\n" \
		                "- What time do I need to leave to arrive in Utrecht at 21:00?\n" \
		                "\n" \
		                "And I will generate an advise for you. \n" \
		                "The good part: Since I am using the website of the NS (the Dutch" \
		                " railway company), my information is as up to date as " \
		                "possible." \
		                "If you need any help in the future, simply type '/help'"
		return self.return_message(return_string)


class NotUnderstoodMessage(Responder):
	def __init__(self):
		super(NotUnderstoodMessage, self).__init__()

	def generate_message(self, *args, **kwargs):
		response = "I'm sorry, I do not know how to handle your current " \
		           "response yet. \n If you wish to know what I can do, type " \
		           "/help."
		return self.return_message({"response": response})


class UnderstandResponse(Responder):
	def __init__(self, ns_api):
		super(UnderstandResponse, self).__init__(ns_api)
		self.ns_api = ns_api
		self.synonym_list = np.genfromtxt('./resources/synonyms.csv')
		self.understood_words = [s[0] for s in self.synonym_list]
		self.new_planning = False

	def generate_message(self, message):
		if self.understood(message) is False:
			return None
		original = self.first_understood_word(message)
		synonym = self.meaning(message)
		if original != synonym:
			response = "With {}, did you mean {}?".format(original, synonym)
			buttons = ["yes", "no"]
			reply = {"response": response, "buttons": buttons}
		else:
			response = "My function working with {} still has to be " \
			           "implemented".format(original)
			self.new_planning = True
			reply = {"response": response}
		return self.return_message(reply)

	def understood(self, message):
		words = [word.strip(string.punctuation) for word in message.split()]
		for word in words:
			if word in self.understood_words:
				return True
			if self.ns_api.is_station(word):
				return True
		return False

	def first_understood_word(self, message):
		words = [word.strip(string.punctuation) for word in message.split()]
		for word in words:
			if word in self.understood_words:
				return word
			if self.ns_api.is_station(word):
				return word
		return None

	def meaning(self, message):
		words = [word.strip(string.punctuation) for word in message.split()]
		for word in words:
			if word in self.understood_words:
				return word
			for synonyms in self.synonym_list:
				if word in synonyms:
					return synonyms[0]
			if self.ns_api.is_station(word):
				return self.ns_api.official_station(word)
		return None


class TravelPlanner(Responder):

	def __init__(self, communicator):
		super(TravelPlanner, self).__init__(communicator)
		self.communicator = communicator
		self.is_planning = False
		self.from_stat = None
		self.to_stat = None
		self.via_stat = None
		self.prev = 0
		self.next = 0
		self.date = ""
		self.depart = True
		self.values_checked = [False for _ in range(7)]

	def generate_message(self, message, start=True):
		if start is True:
			self.is_planning = True
		if self.is_planning is True:
			if False in self.values_checked:
				#TESTING
				advise = self.communicator.ns_api.give_advise({})
				#/TESTING
				reply = self.ask_for_value(self.values_checked.index(False))
				if advise is not None:
					reply = self.advise_string(advise)
		return self.return_message({"response": reply})

	def advise_string(self, lst):
		advise_str = "I have found an advise for you: \n Be in {} at track {} " \
		             "at {}".format(lst[0], lst[1], lst[2])

	def ask_for_value(self, idx_value):
		return None

# TESTING
testing = False
if testing is True:
	bot = BotCommunication(None)
	for i in range(1):
		bot.receive_message("/help")
	while bot.response_waiting is True:
		print(bot.respond())
	print(bot.repeater.log)
