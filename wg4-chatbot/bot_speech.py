import string

import nltk
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
        self.repeater = RepeatAfterMe()
        self.specials = SpecialResponses()
        self.understander = UnderstandResponse(self.ns_api)

    def receive_message(self, messages):
        for message in messages["result"]:
            try:
                text = message["message"]["text"]
                chat_id = message["message"]["chat"]["id"]
                self.messages.append(text)
                self.chat_ids.append(chat_id)
            except Exception as e:
                print(e)
            self.create_response()

    def create_response(self, ):
        """ Creates a response to the message

        TODO:
        - implement responses
        """
        # For now, repeat the message or respond to special texts
        last_message = self.messages[-1]
        last_id = self.chat_ids[-1]
        if last_message in self.specials.special_cases:
            response = self.specials.generate_message(last_message)
        else:
            response = self.understander.generate_message(last_message)
            if response is None:
                response = self.repeater.generate_message(last_message)
        self.update_response(response, last_id)

    def update_response(self, message, chat_id):
        self.send_this.append((message, chat_id))
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
        return self.return_message(message)


class SpecialResponses(Responder):

    def __init__(self):
        super(SpecialResponses, self).__init__()
        self.special_cases = ["/help", "/start"]
        self.special_functions = [self.help, self.start]

    def generate_message(self, message):
        if message not in self.special_cases:
            return self.return_message(None)
        response = self.special_functions[self.special_cases.index(message)]()
        return self.return_message(response)

    def help(self):
        returnstring = "I am the NS chatbot. \n" \
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
        "possible."

        return self.return_message(returnstring)

    def start(self):
        returnstring = " Hello, Nice to see you!\n" \
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
        return self.return_message(returnstring)


class UnderstandResponse(Responder):

    def __init__(self, ns_api):
        super(UnderstandResponse, self).__init__(ns_api)
        self.ns_api = ns_api
        self.synonym_list = np.genfromtxt('./resources/synonyms.csv')
        self.understood_words = [i[0] for i in self.synonym_list]
        pass

    def generate_message(self, message):
        if self.understood(message) is False:
            return None
        original = self.first_understood_word(message)
        synonym = self.meaning(message)
        if original!=synonym:
            response = "With {}, did you mean {}?".format(original, synonym)
        else:
            response = "My function working with {} still has to be " \
                       "implemented".format(original)
        return self.return_message(response)

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




#TESTING
testing = False
if testing is True:
    bot = BotCommunication()
    for i in range(1):
        bot.receive_message("/help")
    while bot.response_waiting is True:
        print(bot.respond())
    print(bot.repeater.log)
