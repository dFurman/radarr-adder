import requests
import json
import os 

class Sonarr:
    def __init__(self, apiKey):
        self.apiKey = apiKey
        self.sonarrIP = os.environ.get('SONARR_IP', 'localhost')

    def get_all_series(self,series_name):
        series_name = series_name.replace(" ", "+")
        r = requests.get(f"http://{self.sonarrIP}:8989/api/series/lookup?term={series_name}&apikey={self.apiKey}")
        return r.json()

    def get_series(self, tvdbId):
        r = requests.get(f"http://{self.sonarrIP}:8989/api/series/lookup?term=tvdb:{tvdbId}&apikey={self.apiKey}")
        return r.json()

    def get_collection(self):
        r = requests.get(f"http://{self.sonarrIP}:8989/api/series?apikey={self.apiKey}")
        return r.json()

    def add_series(self, tvdbId, seasons):
        r = requests.get(f"http://{self.sonarrIP}:8989/api/series/lookup?term=tvdb:{tvdbId}&apikey={self.apiKey}")
        data = r.json()[0]
        series_info = {}
        series_info['apikey'] = self.apiKey
        series_info['title'] = data['title']
        series_info['profileId'] = 4
        series_info['titleSlug'] = data['titleSlug']
        series_info['images'] = data['images']
        series_info['tvdbId'] = data['tvdbId']
        series_info['seasonFolder'] = True
        series_info['seasons'] = seasons
        series_info['addOptions'] = {"searchForMovie": True}
        series_info['rootFolderPath'] = "/tv/"
        series_info['addOptions'] = {"searchForMissingEpisodes": True}
        r = requests.post(f"http://{self.sonarrIP}:8989/api/series?apikey={self.apiKey}", json.dumps(series_info))
        if r.status_code in [200, 201, 202]:
            return "OK"
        elif r.status_code == 400:
            my_collection = self.get_collection()
            for series in my_collection:
                if series['tvdbId'] == tvdbId:
                    series_info = series
                    series_info['seasons'] = seasons
                    r = requests.put(f"http://{self.sonarrIP}:8989/api/series?apikey={self.apiKey}", json.dumps(series_info))
                    if r.status_code in [200, 201, 202]:
                        return "EXISTS"

            return "UNKNOWN"
        else:
            return "UNKNOWN"
