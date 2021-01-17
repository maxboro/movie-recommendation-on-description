import telebot
import spacy
import pandas as pd

testing = True

nlp = spacy.load('en_core_web_sm')

class MixIn:
    
    def description_tags_extraction(self, text: str) -> set:
        if type(text) == str:
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
            tags.update(self.__plural_processing(doc))
        else:
            tags = set()
        return tags
    
    def __plural_processing(self, doc: spacy.tokens.doc.Doc) -> set:
        plural_converted = set()
        for token in doc:
            if token.tag_ in {'NNS', 'NNPS'}:
                plural_converted.add(token.lemma_.lower())
        return plural_converted

'''
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
'''
    
class MovieCollection(MixIn):
    
    def __init__(self, data: pd.DataFrame = None):
        if type(data) == pd.DataFrame and not data.empty:
            self.df = data
        elif type(data) == pd.Series:
            self.df = pd.DataFrame(data).T
        else:
            raise TypeError('Incorrect type in MovieCollection init')
        self.df['tags'] = self.df['description'].apply(self.description_tags_extraction)
    
    def __repr__(self):
        films_to_show = []
        for i in range(len(self.df)):
            line = self.df.iloc[i]
            films_to_show.append(f'{line["title"]} ({line["year"]}, {line["country"]}). {line["description"]}')
        return '\n\n'.join(films_to_show)
    
    def __getitem__(self, key):
        return MovieCollection(self.df.iloc[key])
    
    
    def __tags_similarity_score_for_movie(self, search_tags: set, movie_tags: set) -> float:
        intersect_len = len(movie_tags.intersection(search_tags))
        union_len = len(movie_tags.union(search_tags))
        if union_len > 0:
            return intersect_len / union_len
        else:
            return 0
    
    def tags_similarity_score_collection(self, search_tags):
        self.df['tag_similarity_score'] = self.df['tags'].apply(
                self.__tags_similarity_score_for_movie, 
                args = (search_tags,)
                )
        self.df['general_score'] = self.df['tag_similarity_score'] * self.df['avg_vote']
         
    def sort(self, by: str, asc: bool):
        self.df.sort_values(by = by, axis = 0, inplace= True, ascending = asc)

class Talker(MixIn):
    
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
        bot.send_message(self.chat_id, 'Write a few of your favourite films, separated by semicolumn')
        self.regime = 'favorite'
    
    def description(self, bot):
        bot.send_message(self.chat_id, 'Write film on what themes you want to watch')
        self.regime = 'description'
    
    def subset_of_movies_based_on_tags(self, tags: set) -> MovieCollection:
        self.movie_collection.tags_similarity_score_collection(tags)
        return self.movie_collection[self.movie_collection['general_score'] > 0]
    
    def head_of_sorted_subset_of_movies(self, subset: MovieCollection, num_of_values: int) -> MovieCollection:
        subset.sort(by = 'general_score', asc = False)
        return subset[:num_of_values]
        
        
    def message_processing(self, message: telebot.types.Message):
        if self.regime == 'favorite':
            self.tags = self.__favorite_tags_extraction(message)
        elif self.regime == 'description':
            self.tags = self.description_tags_extraction(message)
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
                }
        )

if testing:
    df = df.head(1000)
        
print('Data is read')   
        
full_collection = MovieCollection(df)
print('Collection is created')

bot = telebot.TeleBot('1495438867:AAFChjHlaG_rWHaY_mY_onekMRwpytHZDRw')
talker = Talker(full_collection)

@bot.message_handler(commands=['start'])
def start_message(message):
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
    else:
        raise Exception("Button error")
    
print('ok')

bot.polling(none_stop=True, interval=0)
        

    