from radarr import Radarr
from sonarr import Sonarr
import telegram
from telegram import (ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
import logging
from imdb import IMDb
import os 

if os.path.isfile('.env'):
    from dotenv import load_dotenv
    load_dotenv()

radarrApiKey = os.environ.get('RADARR_API_KEY')
sonarrApiKey = os.environ.get('SONARR_API_KEY')
telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
raddar = Radarr(radarrApiKey)
sonarr = Sonarr(sonarrApiKey)
seasons_to_add_global = {}
manager_id = int(os.environ.get('MANAGER_ID'))  # Telegram manager id
manager_username = os.environ.get('MANAGER_USERNAME')
gf_username = os.environ.get('GF_USERNAME')
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

Movies, Series = range(2)

def start(update, context):
    button_list = [
        [InlineKeyboardButton("Movies", callback_data=f"MOVIES"),
         InlineKeyboardButton("TV Series", callback_data=f"TV_SERIES")]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)
    user = update.message.from_user
    logger.info(f"{user.first_name} Started a conversation.")
    if user.username == manager_username:
        update.message.reply_text(f'Welcome My King, what would you like to search ?', reply_markup=reply_markup)
        # return Movies
    elif user.username == gf_username:
        update.message.reply_text(f'Welcome My Queen, what would you like to search ?', reply_markup=reply_markup)
        # return Movies
    else:  # Unauthorized Access will be blocked
        logger.info(f"User {user.username} just tried to start a conversation but failed")
        update.message.reply_text(f"Who are you ? I don't know you!")


def search_movies(update, context):
    bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    user = update.message.from_user
    logger.info(f"{user.first_name} Requested to search the Movie: {update.message.text}.")
    movies = raddar.get_movies(update.message.text)
    max_movies = 10  # Radarr returns maximum 20 movies but I want to see first 10 if there are more.
    num_movies = len(movies)
    if num_movies > max_movies:
        update.message.reply_text(f"Found {num_movies} Movies but showing you newest {max_movies}:")
    else:
        update.message.reply_text(f"Found {num_movies} Movies:")
    movies.sort(key=lambda x: x['year'], reverse=True)
    list_movies(update.message.chat_id, movies[:max_movies])

    if num_movies > max_movies:
        button_list = [
            [InlineKeyboardButton("Show All", callback_data=f"SHOWALL_{update.message.text}_{max_movies}")]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Show All Movies ?", reply_markup=reply_markup)
    return Movies

def search_series(update, context):
    bot.send_chat_action(chat_id=update.message.chat_id, action=telegram.ChatAction.TYPING)
    user = update.message.from_user
    logger.info(f"{user.first_name} Requested to search the Series: {update.message.text}.")
    all_series = sonarr.get_all_series(update.message.text)
    max_series = 5  # Radarr returns maximum 20 movies but I want to see first 10 if there are more.
    num_series = len(all_series)
    if num_series > max_series:
        update.message.reply_text(f"Found {num_series} TV Shows but showing you only {max_series}:")
    else:
        update.message.reply_text(f"Found {num_series} TV Shows:")
    list_series(update.message.chat_id, all_series[:max_series])

    if num_series > max_series:
        button_list = [
            [InlineKeyboardButton("Show All", callback_data=f"SHOWALL_{update.message.text}_{max_series}")]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Show All TV Shows ?", reply_markup=reply_markup)
    return Series

def list_movies(chat_id, movies):  # Show the list of movies with Add and More Info buttons
    for movie in movies:
        bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        button_list = [
            [InlineKeyboardButton("Add to Radarr", callback_data=f"ADD_{movie['tmdbId']}"),
             InlineKeyboardButton("More Info...", callback_data=f"MORE_{movie['tmdbId']}")]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        photo_url = movie['images'][0]['url'] if movie['images'][0]['url'] != "http://image.tmdb.org/t/p/original" else open("poster-dark.png", "rb")
        bot.send_photo(chat_id=chat_id, photo=photo_url,
                       caption=f"{movie['title']} ({movie['year']})", reply_markup=reply_markup)

def list_series(chat_id, series_list):
    for series in series_list:
        bot.send_chat_action(chat_id=chat_id, action=telegram.ChatAction.TYPING)
        button_list = [
            [InlineKeyboardButton("Add to Sonarr", callback_data=f"ADD_{series['tvdbId']}"),
             InlineKeyboardButton("More Info...", callback_data=f"MORE_{series['tvdbId']}")]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        posters = list(filter(lambda x: x['coverType'] == 'poster', series['images']))
        photo_url = posters[0]['url'] if len(posters) > 0 else open("poster-dark.png", "rb")
        bot.send_photo(chat_id=chat_id, photo=photo_url,
                       caption=f"{series['title']} ({series['year']})", reply_markup=reply_markup)


def show_more_movie_info(update, movie):  # Show more info about a movie
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=telegram.ChatAction.TYPING)
    button_list = [
        [InlineKeyboardButton("Add to Radarr", callback_data=f"ADD_{movie['tmdbId']}")]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)

    try:
        _imdb = imdb.get_movie(movie['imdbId'].lstrip("tt")) if 'imdbId' in movie else None
    except:
        _imdb = None
    # photo_url = movie['images'][0]['url'] if movie['images'][0]['url'] != "http://image.tmdb.org/t/p/original" else open("poster-dark.png", "rb")
    bot.edit_message_caption(message_id=update.callback_query.message.message_id,
                             chat_id=update.callback_query.message.chat_id,
                             reply_markup=reply_markup,
                             caption=f"""Title: {movie['title']} ({movie['year']}).
Overview: {movie['overview']}

Trailer: {'https://www.youtube.com/watch?v=' + movie['youTubeTrailerId'] if 'youTubeTrailerId' in movie else 'NULL'}

IMDb: {str(_imdb.data['rating']) + '/10' if _imdb and 'rating' in _imdb.data else 'NULL'}
                                   """)

def show_more_series_info(update, series):  # Show more info about a movie
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=telegram.ChatAction.TYPING)
    button_list = [
        [InlineKeyboardButton("Add to Sonarr", callback_data=f"ADD_{series['tvdbId']}")]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)

    try:
        _imdb = imdb.get_movie(series['imdbId'].lstrip("tt")) if 'imdbId' in series else None
    except:
        _imdb = None
    # photo_url = movie['images'][0]['url'] if movie['images'][0]['url'] != "http://image.tmdb.org/t/p/original" else open("poster-dark.png", "rb")
    bot.edit_message_caption(message_id=update.callback_query.message.message_id,
                             chat_id=update.callback_query.message.chat_id,
                             reply_markup=reply_markup,
                             caption=f"""Title: {series['title']} ({series['year']}).
Seasons: {series['seasonCount']}
Network: {series['network']}
IMDb: {str(_imdb.data['rating']) + '/10' if _imdb and 'rating' in _imdb.data else 'NULL'}

Overview: {series['overview']}
""")

# if other user than manager tries to add a movie, send the request to the manager to
# approve and notify the user upon approval
def send_movie_to_manager(movie, user):
    button_list = [
        [InlineKeyboardButton("Add to Radarr", callback_data=f"ACCEPT_{movie['tmdbId']}_{user.id}"),
         InlineKeyboardButton("More Info...", callback_data=f"MORE_{movie['tmdbId']}")]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)
    photo_url = movie['images'][0]['url'] if movie['images'][0][
                                                 'url'] != "http://image.tmdb.org/t/p/original" else open(
        "poster-dark.png", "rb")
    bot.send_photo(chat_id=manager_id, photo=photo_url,
                   caption=f"""Sorry to bother you but {user.first_name} wants to add this movie to your collection:
{movie['title']} ({movie['year']})""",
                   reply_markup=reply_markup)

    return

def add_movie_to_radarr(movie, update):
    chat_id = update.callback_query.message.chat_id
    response = raddar.add_movie(movie['tmdbId'])
    if response == 'OK':
        added_text = f"Excellent Choice! Adding {movie['title']} to your collection."
    elif response == 'EXISTS':
        added_text = f"Just so you know, the movie {movie['title']} is already exists in your collection :)"
    elif response == 'UNKNOWN':
        added_text = f"I'm sorry to tell you that something went wrong while trying to add the movie and I don't know what :\\"

    bot.edit_message_caption(message_id=update.callback_query.message.message_id,
                             chat_id=chat_id,
                             caption=f"""{update.callback_query.message.caption}

{added_text}""")

def check_if_season_exists(tvdbId):
    my_collection = sonarr.get_collection()
    for series in my_collection:
        if series['tvdbId'] == tvdbId:
            seasons = []
            for season in series['seasons']:
                seasons.append({'seasonNumber': season['seasonNumber'], 'monitored': season['monitored']})
            return seasons
    return False

def update_series_button_list(tvdbId):
    button_list = []
    for season in seasons_to_add_global[tvdbId][1:]:
        if season['monitored'] is True:
            button_list.append([InlineKeyboardButton(f"Remove Season {season['seasonNumber']}",
                                                     callback_data=f"REMOVESEASON_{tvdbId}_{season['seasonNumber']}")])
        else:
            button_list.append([InlineKeyboardButton(f"Add Season {season['seasonNumber']}",
                                                     callback_data=f"ADDSEASON_{tvdbId}_{season['seasonNumber']}")])
    return button_list

def edit_series_message_with_new_button_list(message, new_button_list, tvdbId):
    new_button_list.append([InlineKeyboardButton(f"Done !", callback_data=f"ADDSERIES_{tvdbId}")])
    new_button_list.append([InlineKeyboardButton(f"Cancel", callback_data=f"CANCEL_123")])
    reply_markup = InlineKeyboardMarkup(new_button_list)

    bot.edit_message_caption(message_id=message.message_id,
                             chat_id=message.chat_id,
                             reply_markup=reply_markup,
                             caption=message.caption)

def add_series_to_sonarr(series, update):
    seasons_to_add = check_if_season_exists(series['tvdbId'])
    if not seasons_to_add:
        seasons_to_add = []
        for i in range(series['seasonCount']+1):
            seasons_to_add.append({"seasonNumber": i, "monitored": False})
    seasons_to_add_global[series['tvdbId']] = seasons_to_add
    button_list = update_series_button_list(series['tvdbId'])
    edit_series_message_with_new_button_list(update.callback_query.message, button_list, series['tvdbId'])

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)
    bot.send_message(chat_id=manager_id,
                     text=f'Update ${update} caused error "${context.error}"')

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope I helped you today :)',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def select_source_query_handler(update, context):
    bot.send_message(chat_id=update.callback_query.message.chat_id,
                     text=f"Awesome, now enter what do you want to search:")
    cqd = update.callback_query.data
    if cqd == "MOVIES":
        return Movies
    elif cqd == "TV_SERIES":
        return Series
    else:
        return cancel(update,context)

def series_callback_query_handler(update, context):
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=telegram.ChatAction.TYPING)
    cqd = update.callback_query.data
    user = update.callback_query.from_user
    message = update.callback_query.message
    split = cqd.split("_")
    action = split[0]
    tvdbId = data = int(split[1])
    if not action == 'CANCEL':
        series = sonarr.get_series(tvdbId)[0]
    if action == 'ADD':
        if user.id != manager_id:
            bot.send_message(chat_id=message.chat_id,
                             text=f"Great, I'll let the King know you want to add this series :)")
            # send_series_to_manager(series, user)
        else:
            add_series_to_sonarr(series, update)

    elif action == 'MORE':
        logger.info(f"The User {user.first_name} requested to see more details about the Series {series['title']}")
        show_more_series_info(update, series)

    elif action == 'ADDSEASON':
        season_number=split[2]
        seasons_to_add_global[tvdbId][int(season_number)]['monitored'] = True
        new_button_list = update_series_button_list(tvdbId)
        edit_series_message_with_new_button_list(message, new_button_list, tvdbId)

    elif action == 'REMOVESEASON':
        season_number=split[2]
        seasons_to_add_global[tvdbId][int(season_number)]['monitored'] = False
        new_button_list = update_series_button_list(tvdbId)
        edit_series_message_with_new_button_list(message, new_button_list, tvdbId)


    elif action == 'ADDSERIES':
        response = sonarr.add_series(tvdbId, seasons_to_add_global[tvdbId])
        if response == 'OK':
            added_text = f"Excellent Choice! Adding {series['title']} to your collection."
        elif response == 'EXISTS':
            added_text = f"Cool, I updated your collection :)"
        elif response == 'UNKNOWN':
            added_text = f"I'm sorry to tell you that something went wrong while trying to add the Series and I don't know what :\\"

        bot.edit_message_caption(message_id=message.message_id, chat_id=message.chat_id,
                                 caption=added_text)

    elif action == 'ACCEPT':
        series = sonarr.get_series(tvdbId)[0]
        user_to_notify = split[2]
        bot.send_message(chat_id=user_to_notify,
                         text=f"Congratulations! The King has approved your request for the TV Show: {series['title']}")
        sonarr.add_series(tvdbId, seasons_to_add_global[tvdbId])

    elif action == 'CANCEL':
        bot.edit_message_caption(message_id=message.message_id, chat_id=message.chat_id,
                                 caption="Canceled")

def movies_callback_query_handler(update, context):
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=telegram.ChatAction.TYPING)
    cqd = update.callback_query.data
    user = update.callback_query.from_user
    split = cqd.split("_")
    action = split[0]
    tmdbId = data = split[1]
    movie = raddar.get_movie(tmdbId)
    if action == 'ADD':
        if user.id != manager_id:
            bot.send_message(chat_id=update.callback_query.message.chat_id,
                             text=f"Great, I'll let the King know you want to add this movie :)")
            send_movie_to_manager(movie, user)
        else:
            add_movie_to_radarr(movie, update)

    elif action == 'MORE':
        logger.info(f"The User {user.first_name} requested to see more details about the movie {movie['title']}")
        show_more_movie_info(update, movie)

    elif action == 'ACCEPT':
        user_to_notify = split[2]
        bot.send_message(chat_id=user_to_notify,
                         text=f"Congratulations! The King has approved your request for the movie: {movie['title']}")
        add_movie_to_radarr(movie, update)


    elif action == 'SHOWALL':
        max_movies = int(split[2])
        movies = raddar.get_movies(data)
        movies.sort(key=lambda x: x['year'], reverse=True)
        list_movies(update.callback_query.message.chat_id, movies[max_movies:])

    return Movies

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(telegram_bot_token, use_context=True)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      CallbackQueryHandler(select_source_query_handler)],

        states={
            Movies: [MessageHandler(Filters.text, search_movies),
                     CallbackQueryHandler(movies_callback_query_handler),
                     # CommandHandler('start', start)
                     ],
            Series: [MessageHandler(Filters.text, search_series),
                     CallbackQueryHandler(series_callback_query_handler),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    bot = telegram.Bot(token=telegram_bot_token)
    imdb = IMDb()
    main()