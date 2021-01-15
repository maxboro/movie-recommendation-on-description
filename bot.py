import telebot
import spacy
import pandas as pd

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
                })
nlp = spacy.load('en_core_web_sm')

class Movie:
    
    def __init__(self, line: pd.Series):
        parameter_dict = line.to_dict()
        self.imdb_title_id = parameter_dict['imdb_title_id']
        self.year = parameter_dict['year']
        self.genre = parameter_dict['genre'].split(',')
        self.country = parameter_dict['country'].split(',')
        self.description = parameter_dict['description']
        self.avg_vote = parameter_dict['avg_vote']
        self.votes = parameter_dict['votes']
        self.title = parameter_dict['title']
        self.tags = self.__tags_extraction(self.description)
    
    def __tags_extraction(self, text: str) -> set:
        doc = nlp(text)
        tags = {
                token.text.lower() 
                for token in doc 
                    if (token.text.lower() not in nlp.Defaults.stop_words) 
                    and (not token.is_punct)
                    and (not token.is_digit)
                }
        noun_chunks = {
                token.text.lower()
                for token in doc.noun_chunks
                    if token.text.lower() not in nlp.Defaults.stop_words
                }
        tags.update(noun_chunks)
        return tags
    
    def plot_description_similarity(self, movie: 'Movie object') -> float:
        intersect_len = len(self.tags.intersect(movie.tags))
        union_len = len(self.tags.union(movie.tags))
        return intersect_len / union_len
    
class MovieCollection :
    
    def __init__(self, df: pd.DataFrame):
        self.films = []
        for i in range(len(df)):
            self.films.append(Movie(df.iloc[i]))

class Talker:
    
    def __init__(self):
        pass
    
    def beginning(self, bot: telebot.TeleBot, message: telebot.types.Message):
        self.chat_id = message.from_user.id
        keyboard = telebot.types.InlineKeyboardMarkup()  
        key_user_desc = telebot.types.InlineKeyboardButton(text='Recommend movies from description', callback_data='description') 
        keyboard.add(key_user_desc)
        key_user_fav = telebot.types.InlineKeyboardButton(text='Recommend movies like your favorite movies', callback_data='favorite') 
        keyboard.add(key_user_fav)
        bot.send_message(self.chat_id, text='How you prefer to get recommendations', reply_markup=keyboard)
    
    def favorite(self, bot, call):
        print('favorite')
        bot.send_message(self.chat_id, 'Write a few of your favourite films, separated by semicolumn')
    
    def description(self, bot, call):
        print('description')
        bot.send_message(self.chat_id, 'Write film on what themes you want to watch')
    
    def message_processing(self, message):
        pass

talker = Talker()
bot = telebot.TeleBot('')

@bot.message_handler(commands=['start'])
def start_message(message):
    talker.beginning(bot, message)
    
@bot.message_handler(content_types=['text']) 
def get_text_messages(message):
    talker.message_processing(message)
    
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "favorite":
        talker.favorite(bot, call)
    elif call.data == "description":
        talker.description(bot, call)
    
print('ok')

bot.polling(none_stop=True, interval=0)
        

    