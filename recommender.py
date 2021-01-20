import telebot
import spacy
import numpy as np
import pandas as pd



class MixIn:
    
    nlp = spacy.load('en_core_web_sm')
    
    def description_tags_extraction(self, text: str) -> set:
        if type(text) == str:
            doc = self.nlp(text)
            tags = {
                token.lemma_ 
                for token in doc 
                if (token.text.lower() not in self.nlp.Defaults.stop_words) 
                    and (not token.is_punct)
                    and (not token.is_digit)
                    and token.text.lower() not in {'smth'}
                    }
            noun_chunks = {
                token.text.lower()
                for token in doc.noun_chunks
                    if token.text.lower() not in self.nlp.Defaults.stop_words
                    }
            tags.update(noun_chunks)
        else:
            tags = set()
        return tags
    
  

    
class MovieCollection(MixIn):
    
    def __init__(self, data: pd.DataFrame = None):
        if type(data) == pd.DataFrame and not data.empty:
            self.df = data
        elif type(data) == pd.Series:
            self.df = pd.DataFrame(data).T
        else:
            raise TypeError(f'Incorrect type in MovieCollection init. {type(data)}: {data}')
        self.df['tags'] = self.df['description'].apply(self.description_tags_extraction)
    
    def __repr__(self):
        films_to_show = []
        for i in range(len(self.df)):
            line = self.df.iloc[i]
            films_to_show.append(f'{line["original_title"]} ({line["year"]}, {line["country"]}). ' +
                                      f'{line["description"]} Vote - {line["avg_vote"]}')
        return '\n\n'.join(films_to_show)
    
    def __getitem__(self, key):
        return MovieCollection(self.df.iloc[key])
    
    def __len__(self):
        return len(self.df)
    
    def __tags_similarity_score_for_movie(self, search_tags: set, movie_tags: set) -> float:
        intersect_len = len(movie_tags.intersection(search_tags))
        search_len = len(search_tags)
        if search_len > 0:
            return intersect_len / search_len
        else:
            return 0
    
    def tags_similarity_score_collection(self, search_tags):
        self.df['tag_similarity_score'] = self.df['tags'].apply(
                self.__tags_similarity_score_for_movie, 
                args = (search_tags,)
                )
        self.df['general_score'] = np.sqrt(self.df['tag_similarity_score']) * self.df['avg_vote']*0.1
         
    def sort(self, by: str, asc: bool):
        self.df.sort_values(by = by, axis = 0, inplace= True, ascending = asc)

class Talker(MixIn):
    
    def __init__(self, movie_collection: MovieCollection, testing: bool):
        self.movie_collection = movie_collection
        self.testing = testing
    
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
        if self.testing:
            display(self.movie_collection.df.head(10))
            print(f'First movie tags: {self.movie_collection.df["tags"][0]}')
        query_result = self.movie_collection.df[self.movie_collection.df['general_score'] > 0]
        if not query_result.empty:
            return MovieCollection(query_result)
        else:
            return None
    
    def head_of_sorted_subset_of_movies(self, subset: MovieCollection, num_of_values: int) -> MovieCollection:
        if type(subset) == MovieCollection and type(num_of_values) == int:
            subset.sort(by = 'general_score', asc = False)
            return subset[:num_of_values]
        else:
            raise TypeError(f'''Wrong type in Talker.head_of_sorted_subset_of_movies method. 
                            Subset type: {type(subset)}
                            num_of_values type:{type(head_of_sorted_subset_of_movies)}''')
        
        
    def message_processing(self, bot, message: telebot.types.Message):
        if self.regime == 'favorite':
            self.tags = self.__favorite_tags_extraction(message)
        elif self.regime == 'description':
            self.tags = self.description_tags_extraction(message.text)
        else:
            raise ValueError(f'Something wrong with Talker.regime value in Talker.message_processing method. Value: {regime}')
        
        if self.testing: print(f'Search tags: {self.tags}')
        subset = self.subset_of_movies_based_on_tags(self.tags)
        
        if subset:
            head_of_subset = self.head_of_sorted_subset_of_movies(subset, 5)
            bot.send_message(self.chat_id, str(head_of_subset))
        else:
            bot.send_message(self.chat_id, "No such movies in base")
             

