from radarr import Radarr
import telegram
from telegram import (ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)
import logging
from imdb import IMDb


raddarApiKey = ''
telegram_bot_token = ':'
raddar = Radarr(raddarApiKey)
manager_id =   # Telegram manager id (int)
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

MovieName = range(1)

def start(update, context):
    user = update.message.from_user
    logger.info(f"{user.first_name} Started a conversation.")
    if user.username == "":  # Manager Username
        update.message.reply_text(f'Welcome My King, what movie would you like to search ?')
        return MovieName
    elif user.username == "":  # GF Username
        update.message.reply_text(f'Welcome My Queen, what movie would you like to search ?')
        return MovieName
    else:  # Unauthorized Access will be blocked
        logger.info(f"User {user.username} just tried to start a conversation but failed")
        update.message.reply_text(f"Who are you ? I don't know you!")


def show_movies(chat_id, movies):  # Show the list of movies with Add and More Info buttons
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


def show_more_info(update, movie):  # Show more info about a movie
    bot.send_chat_action(chat_id=update.callback_query.message.chat_id, action=telegram.ChatAction.TYPING)
    button_list = [
        [InlineKeyboardButton("Add to Radarr", callback_data=f"ADD_{movie['tmdbId']}")]
    ]
    reply_markup = InlineKeyboardMarkup(button_list)

    _imdb = imdb.get_movie(movie['imdbId'].lstrip("tt")) if 'imdbId' in movie else None
    photo_url = movie['images'][0]['url'] if movie['images'][0]['url'] != "http://image.tmdb.org/t/p/original" else open("poster-dark.png", "rb")
    bot.send_photo(chat_id=update.callback_query.message.chat_id, photo=photo_url, reply_markup=reply_markup,
                   caption=f"""Title: {movie['title']} ({movie['year']}).
Overview: {movie['overview']}

Trailer: {'https://www.youtube.com/watch?v=' + movie['youTubeTrailerId'] if 'youTubeTrailerId' in movie else 'NULL'}

IMDb: {str(_imdb.data['rating']) + '/10' if _imdb and 'rating' in _imdb.data else 'NULL'}
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

def movie_name(update, context):
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
    show_movies(update.message.chat_id, movies[:max_movies])

    if num_movies > max_movies:
        button_list = [
            [InlineKeyboardButton("Show All", callback_data=f"SHOWALL_{update.message.text}_{max_movies}")]
        ]
        reply_markup = InlineKeyboardMarkup(button_list)
        bot.send_message(chat_id=update.message.chat_id,
                         text=f"Show All Movies ?", reply_markup=reply_markup)
    return MovieName

def error(update, context):
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def cancel(update, context):
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text('Bye! I hope I helped you today :)',
                              reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def callback_query_handler(update, context):
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
            bot.send_message(chat_id=update.callback_query.message.chat_id,
                             text=f"Excellent Choice! Adding {movie['title']} to your collection.")
            raddar.add_movie(tmdbId)

    elif action == 'MORE':
        logger.info(f"The User {user.first_name} requested to see more details about the movie {movie['title']}")
        show_more_info(update, movie)

    elif action == 'ACCEPT':
        user_to_notify = split[2]
        bot.send_message(chat_id=update.callback_query.message.chat_id,
                         text=f"Excellent Choice! Adding {movie['title']} to your collection.")
        bot.send_message(chat_id=user_to_notify,
                         text=f"Congratulations! The King has approved your request for the movie: {movie['title']}")
        raddar.add_movie(tmdbId)

    elif action == 'SHOWALL':
        max_movies = int(split[2])
        movies = raddar.get_movies(data)
        movies.sort(key=lambda x: x['year'], reverse=True)
        show_movies(update.callback_query.message.chat_id, movies[max_movies:])

    return MovieName

def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(telegram_bot_token, use_context=True)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Add conversation handler with the states
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            MovieName: [MessageHandler(Filters.text, movie_name),
                        CallbackQueryHandler(callback_query_handler),
                        CommandHandler('start', start)]
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