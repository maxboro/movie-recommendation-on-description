import time
from recommender import * 

testing = True

bot = telebot.TeleBot('')  #token 

df = pd.read_csv(
        'movies_info.csv',
        dtype= {
                'imdb_title_id': 'object',
                'title':'object',
                'original_title':'object',
                'year':'object',
                'genre':'object',
                'country':'object',
                'description':'object',
                'avg_vote':'float64',
                'votes':'int64'
                }
        )

if testing:
    df = df.head(1000)
    pd.set_option('display.max_columns', 30)
else:
    to_int = lambda x: int(x) if x.isnumeric() else 0   
    df['year'] = df['year'].apply(to_int)
    df = df[(df['votes'] > 1400) & (df['year'] > 1935)]
    df = df.sort_values(by=['avg_vote'], ascending=False).head(12000)
        
print('Data is read')   
        
full_collection = MovieCollection(df)
print('Collection is created')
regime_manager = RegimeManager(bot)
bot_on = False

@bot.message_handler(commands=['start'])
def start_message(message):
    regime_manager.beginning(message)
    global bot_on
    bot_on = True
    
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data in {'favorite', 'description'}:
        global talker
        talker = regime_manager.returnBot(
                call = call, 
                movie_collection = full_collection, 
                testing = testing, 
                telebot = bot
                )
    else:
        talker.add_tags_in_multiple_movies_with_same_name_situation(movie_id = call.data)

@bot.message_handler(content_types=['text']) 
def get_text_messages(message):
    try:
        start = time.time()
        talker.message_processing(message)
        talker.send_message(f'search time: {round(time.time() - start, 1)} s')
    except NameError:
        if bot_on:
            bot.send_message(message.from_user.id, text="Please choose the mode of bot\'s work")
        else:
            bot.send_message(message.from_user.id, text='To run the bot send "\\start" command')

    
print('ok')

bot.infinity_polling()
        
#bot.polling(none_stop=True, interval=0)
    