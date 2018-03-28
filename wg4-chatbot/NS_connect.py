import json
import requests
import time
import urllib

from io import StringIO

import config
import urllib.parse
from xml.etree import ElementTree
import xmltodict

class NS_info:

    def __init__(self):
        self.auth = (config.NS_UN, config.NS_WW)
        self.list_of_stations = self.get_list_of_stations(self.auth)
        for station in self.list_of_stations:
            print(station[0])

    def get_list_of_stations(self, auth = (None, None)):
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
                    print(type(synonyms))
                    list_of_station_names.append(synonyms)
            list_of_stations.append(list_of_station_names)
        return list_of_stations


    def get_dict_of_stations(self, auth = (None, None)):
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
            if word in station:
                return True
        return False

    def official_station(self, word):
        for station in self.list_of_stations:
            if word in station:
                return station[2]
        return None