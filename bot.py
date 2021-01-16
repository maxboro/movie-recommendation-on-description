import telebot
import spacy
import pandas as pd

nlp = spacy.load('en_core_web_sm')

def description_tags_extraction(text: str) -> set:
    doc = nlp(text)
    tags = {
            token.text.lower() 
            for token in doc 
            if (token.text.lower() not in nlp.Defaults.stop_words) 
                and (not token.is_punct)
                and (not token.is_digit)
                and token.text.lower() not in {'about'}
            }
    noun_chunks = {
            token.text.lower()
            for token in doc.noun_chunks
                if token.text.lower() not in nlp.Defaults.stop_words
                }
    tags.update(noun_chunks)
    return tags


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
        self.tags = description_tags_extraction(self.description)
    
    
    def plot_description_similarity(self, movie: 'Movie object') -> float:
        intersect_len = len(self.tags.intersect(movie.tags))
        union_len = len(self.tags.union(movie.tags))
        return intersect_len / union_len
    
class MovieCollection:
    
    def __init__(self, data: pd.DataFrame = None):
        self.films = []
        if type(data) == pd.DataFrame and not data.empty:
            for i in range(len(data)):
                self.films.append(Movie(data.iloc[i]))
    
    def __repr__(self):
        films_to_show = []
        for movie in self.films:
            films_to_show.append(f'{movie.title} ({movie.year}, {",".join(movie.country)}). {movie.description}')
        return '\n\n'.join(films_to_show)
    
    def __getitem__(self, key):
        return self.films[key]
    
    def append(self, movie: Movie):
        if type(movie) == Movie:
            self.films.append(movie)
        else:
            raise TypeError('Append method can be used only to Movies')
            
    def sort(self, on: str, asc: bool):
        pass

class Talker:
    
    def __init__(self, movie_collection: MovieCollection):
        self.movie_collection = movie_collection
    
    def beginning(self, bot: telebot.TeleBot, message: telebot.types.Message):
        self.chat_id = message.from_user.id
        keyboard = telebot.types.InlineKeyboardMarkup()  
        key_user_desc = telebot.types.InlineKeyboardButton(text='Recommend movies from description', callback_data='description') 
        keyboard.add(key_user_desc)
        key_user_fav = telebot.types.InlineKeyboardButton(text='Recommend movies like your favorite movies', callback_data='favorite') 
        keyboard.add(key_user_fav)
        bot.send_message(self.chat_id, text='How you prefer to get recommendations', reply_markup=keyboard)
    
    def favorite(self, bot):
        print('favorite')
        bot.send_message(self.chat_id, 'Write a few of your favourite films, separated by semicolumn')
        self.regime = 'favorite'
    
    def description(self, bot):
        print('description')
        bot.send_message(self.chat_id, 'Write film on what themes you want to watch')
        self.regime = 'description'
    
    def subset_of_movies_based_on_tags(self, collection: MovieCollection, tags: set) -> MovieCollection:
        pass
    
    def head_of_sorted_subset_of_movies(self, subset: MovieCollection, num_of_values: int) -> MovieCollection:
        pass
        
        
    def message_processing(self, message: telebot.types.Message):
        if self.regime == 'favorite':
            self.tags = self.__favorite_tags_extraction(message)
        elif self.regime == 'description':
            self.tags = description_tags_extraction(message)
        else:
            raise ValueError('Something wrong with Talker.regime value in Talker.message_processing method')
        
        subset = self.subset_of_movies_based_on_tags(self.tags)
        head_of_subset = self.head_of_sorted_subset_of_movies(subset, 5)
        bot.send_message(self.chat_id, head_of_subset)
        
        
        
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
        
    
        
full_collection = MovieCollection(df)

bot = telebot.TeleBot('')

@bot.message_handler(commands=['start'])
def start_message(message):
    talker = Talker()
    talker.beginning(bot, message)
    
@bot.message_handler(content_types=['text']) 
def get_text_messages(message):
    talker.message_processing(message)
    
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "favorite":
        talker.favorite(bot)
    elif call.data == "description":
        talker.description(bot)
    
print('ok')

bot.polling(none_stop=True, interval=0)
        

    