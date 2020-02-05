# Radarr Telegram Search and Add
[![Build Status](https://travis-ci.com/dFurman/radarr-adder.svg?branch=master)](https://travis-ci.com/dFurman/radarr-adder)

While using my Telegram bot to send me notifications from Radarr I decided to make it also search and add movies to my collection in Radarr (and tv-shows in Sonarr).
It all started from Radarr and thus it's called Radarr-Adder but today its compatible also with sonarr (90% compatible).


#### Features:
1. Restrict access to a specific user name
2. Get a list of movies and tv-shows with the buttons "Add to .." and "More Info"
3. More Info will get you the overview of the movie, trailer (if available) and imdb score (if available)
4. When non-manager wants to add a movie, it sends an approve reqeust to the manager and updates the requesting user once approved.

# Environment Variables

- RADARR_API_KEY 
- SONARR_API_KEY
- TELEGRAM_BOT_TOKEN
- MANAGER_ID (int)
- MANAGER_USERNAME(string)
- GF_USERNAME(string)
- RADARR_IP

![Screenshot1](screenshots/1.jpg)
![Screenshot2](screenshots/2.jpg)
