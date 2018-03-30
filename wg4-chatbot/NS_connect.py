import json
import requests
import urllib
import config
import urllib.parse
import xmltodict


class NS_info:
	def __init__(self):
		self.auth = (config.NS_UN, config.NS_WW)
		self.list_of_stations = self.get_list_of_stations(self.auth)

	def get_list_of_stations(self, auth=(None, None)):
		stations_dict = self.get_dict_of_stations(auth)
		stations_list = stations_dict["Stations"]["Station"]
		list_of_stations = []
		for station in stations_list:
			list_of_station_names = [station["Namen"]["Kort"]]
			list_of_station_names.append(station["Namen"]["Middel"])
			list_of_station_names.append(station["Namen"]["Lang"])
			if station["Synoniemen"] is not None:
				synonyms = station["Synoniemen"]["Synoniem"]
				if isinstance(synonyms, list) is True:
					list_of_station_names.extend(synonyms)
				else:
					list_of_station_names.append(synonyms)
			list_of_stations.append(list_of_station_names)
		return list_of_stations

	def get_dict_of_stations(self, auth=(None, None)):
		stations_URL = "http://webservices.ns.nl/ns-api-stations-v2"
		stations = None
		try:
			# etree.parse(stations_URL)
			stations = requests.get(stations_URL, auth=auth).content.decode()
			stations = xmltodict.parse(stations)
		except Exception as e:
			print(e)
		return stations

	def is_station(self, word):
		for station in self.list_of_stations:
			if self.approximates(word, station):
				return True
		return False

	def official_station(self, word):
		for station in self.list_of_stations:
			if self.approximates(word, station):
				return station[2]
		return None

	def approximates(self, word, station_lst):
		# TODO: implement more ways of approximating
		for station_syn in station_lst:
			if station_syn.lower() == word.lower():
				return True
		return False

	def make_advice_url(self, from_stat='Utrecht Centraal', to_stat='Wierden',
	                    via_stat=None, prev=0, next=0, time=None, depart=True):
		url = "http://webservices.ns.nl/ns-api-treinplanner?fromStation={}&" \
		      "toStation={}&previousAdvices={}&nextAdvices={}&Departure={}".format(
			urllib.parse.quote_plus(bytes(from_stat, 'utf8')),
			urllib.parse.quote_plus(bytes(to_stat, 'utf8')),
			json.dumps(prev),
			json.dumps(next),
			json.dumps(depart))
		if via_stat is not None:
			url += "&viaStation={}".format(urllib.parse.quote_plus(via_stat))
		if time is not None:
			url += "&dateTime={}".format(json.dumps(time))
		print("sending url to ns api: {}".format(url))
		return url

	def give_advise(self, advise_args):
		""" Advice args should be: (from_stat, to_stat, via_stat, prev, next
				time, depart)
				:returns [fromstat, gotime, gotrack, (0..n)*
									[viastat, arrivetime, arrivetrack, gotime, gotrack],
									tostation, totime, totrack]

			"""
		url = self.make_advice_url(**advise_args)
		advice_xml = requests.get(url, auth=self.auth).content.decode()
		advice_dict = xmltodict.parse(advice_xml)
		clean_advice_lst = self.clean_advice(advice_dict)
		return clean_advice_lst

	def clean_advice(self, advise_dict):
		# TODO
		print(advise_dict)
		clean_dict = []
		reis = advise_dict["ReisMogelijkheden"]["ReisMogelijkheid"]
		if isinstance(reis, list):
			reis = reis[0]
		# for key in reis.keys():
		# 	print("{}: {}".format(key, reis[key]))
		reisdeel = reis["ReisDeel"]

		# for deel in reisdeel:
		# 	print("reisdeel:")
		# 	for key in deel.keys():
		# 		print("{}: {}".format(key, deel[key]))
		# 	reis_stop = deel["ReisStop"]
		# 	for stop in reis_stop:
		# 		for key in stop:
		# 			print("{}: {}".format(key, stop[key]))

		from_stat = reis["ReisDeel"][0]["ReisStop"][0]["Naam"]
		from_track = reis["ReisDeel"][0]["ReisStop"][0]["Spoor"]["#text"]
		from_time = reis["ActueleVertrekTijd"][-13:-5]
		via = []
		for deelidx, deel in enumerate(reisdeel[:-1]):
			via_stat = deel["ReisStop"][-1]["Naam"]
			via_in_time = deel["ReisStop"][-1]["Tijd"][-13:-5]
			via_in_track = deel["ReisStop"][-1]["Spoor"]["#text"]
			deel_out = reisdeel[deelidx + 1]
			via_out_time = deel_out["ReisStop"][0]["Tijd"][-13:-5]
			via_out_track = deel_out["ReisStop"][0]["Spoor"]["#text"]
			via.append([via_stat, via_in_time, via_in_track, via_out_time,
			            via_out_track, ])
		to_stat = reis["ReisDeel"][-1]["ReisStop"][-1]["Naam"]
		to_track = reis["ReisDeel"][-1]["ReisStop"][-1]["Spoor"]["#text"]
		to_time = reis["ActueleAankomstTijd"][-13:-5]
		clean_dict = [from_stat, from_track, from_time, via, to_stat, to_track,
		              to_time, ]
		print(clean_dict)
		return clean_dict
