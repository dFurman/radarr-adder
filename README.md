# Radarr Telegram Search and Add

While using my Telegram bot to send me notifications from Radarr I decided to make it also search and add movies to my collection in Radarr.
#### Features:
1. Restrict access to a specific user name
2. Get a list of movies with the buttons "Add to Radarr" and "More Info"
3. More Info will get you the overview of the movie, trailer (if available) and imdb score (if available)
4. When non-manager wants to add a movie, it sends an approve reqeust to the manager and updates the requesting user once approved.


#### Things to change before running the script
**in radarr.py you should change the following:**
- movie_info['qualityProfileId']
- movie_info['rootFolderPath']

**in main.py you should fill the following:**
- raddarApiKey
- telegram_bot_token
- manager_id (Telegram Manager ID)
- Manager Username + GF Username
