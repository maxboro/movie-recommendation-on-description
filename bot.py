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
        
print('Data is read')   
        
full_collection = MovieCollection(df)
print('Collection is created')
    
talker = Talker(movie_collection = full_collection, testing = testing)

@bot.message_handler(commands=['start'])
def start_message(message):
    talker.beginning(bot, message)
    
@bot.message_handler(content_types=['text']) 
def get_text_messages(message):
    talker.message_processing(bot, message)
    
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "favorite":
        talker.favorite(bot)
    elif call.data == "description":
        talker.description(bot)
    else:
        raise Exception("Button error")
    
print('ok')

bot.polling(none_stop=True, interval=0)
        

    