import requests
import json

class Radarr:
    def __init__(self, apiKey):
        self.apiKey = apiKey

    def get_movies(self,movie_name):
        movie_name = movie_name.replace(" ", "+")
        r = requests.get(f"http://localhost:7878/api/movie/lookup?term={movie_name}&apikey={self.apiKey}")
        return r.json()

    def get_movie(self, tmdbId):
        r = requests.get(f"http://localhost:7878/api/movie/lookup/tmdb?tmdbId={tmdbId}&apikey={self.apiKey}")
        return r.json()

    def add_movie(self, tmdbId):
        r = requests.get(f"http://localhost:7878/api/movie/lookup/tmdb?tmdbId={tmdbId}&apikey={self.apiKey}")
        data = r.json()
        movie_info = {}
        movie_info['apikey'] = self.apiKey
        movie_info['title'] = data['title']
        movie_info['qualityProfileId'] = 4
        movie_info['titleSlug'] = data['titleSlug']
        movie_info['images'] = data['images']
        movie_info['tmdbId'] = data['tmdbId']
        movie_info['year'] = data['year']
        movie_info['rootFolderPath'] = "W:\\Movies\\"
        movie_info['monitored'] = True
        movie_info['addOptions'] = {"searchForMovie": True}

        r = requests.post(f"http://localhost:7878/api/movie?apikey={self.apiKey}", json.dumps(movie_info))
        return