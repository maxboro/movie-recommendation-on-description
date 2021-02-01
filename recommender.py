import re
import telebot
import spacy
import numpy as np
import pandas as pd



class TextProcessor:
    
    nlp = spacy.load('en_core_web_sm')
    
    def __noun_chunks_filter(self, noun_chunks: set) -> set:
        chuncks_to_go = set()
        for chunk in noun_chunks:
            chunk_new = re.sub(r'\b(a|the|an)\s+', '', chunk)
            chunk_new = chunk_new.strip()
            chuncks_to_go.add(chunk_new)
        return chuncks_to_go
    
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

            tags.update(self.__noun_chunks_filter(noun_chunks))
        else:
            tags = set()
        return tags
    
    
    def movie_title_processing(self, text: str) -> str:
        text = re.sub(r'\s+', ' ', text.lower().strip())
        return text
    
  

    
class MovieCollection(TextProcessor):
    
    def __init__(self, data: pd.DataFrame = None) -> None:
        if type(data) == pd.DataFrame:
            self.df = data
        elif type(data) == pd.Series:
            self.df = pd.DataFrame(data).T
        else:
            raise TypeError(f'Incorrect type in MovieCollection init. {type(data)}: {data}')
        self.df['tags'] = self.df['description'].apply(self.description_tags_extraction)
        self.df['title_lower'] = self.df['original_title'].apply(self.movie_title_processing)
    
    def __repr__(self) -> str:
        films_to_show = []
        for i in range(len(self.df)):
            line = self.df.iloc[i]
            films_to_show.append(f'{line["original_title"]} ({line["year"]}, {line["country"]}). ' +
                                      f'{line["description"]} Vote - {line["avg_vote"]}')
        return '\n\n'.join(films_to_show)
    
    def __getitem__(self, key):
        if type(key) == str:
            if len(self.df) == 1:
                return self.df[key].values[0]
            else:
                return self.df[key]
        else:    
            return MovieCollection(self.df.iloc[key])
    
    def __len__(self) -> int:
        return len(self.df)
    
    def __tags_similarity_score_for_movie(self, search_tags: set, movie_tags: set) -> float:
        intersect_len = len(movie_tags.intersection(search_tags))
        search_len = len(search_tags)
        if search_len > 0:
            return intersect_len / search_len
        else:
            return 0
    
    def get_id(self, return_list: bool = False) -> (list, str):
        if len(self) > 1 or return_list:
            return self.df['imdb_title_id'].to_list()
        elif len(self) == 1:
            return self.df['imdb_title_id'].values[0]
        else:
            return None
        
    def get_tags(self) -> set:
        tags = set()
        for line_tags in self.df['tags']:
            tags.update(line_tags)
        return tags
    
    def search_by_title(self, title: str):
        title_clean = self.movie_title_processing(title)
        return MovieCollection(self.df[self.df['title_lower'] == title_clean])
    
    def search_by_id(self, movie_id: str):
        return MovieCollection(self.df[self.df['imdb_title_id'] == movie_id])
    
    def removed_by_id(self, movie_id: (str, list)):
        if type(movie_id) == list:
            if movie_id:
                return MovieCollection(self.df[~self.df['imdb_title_id'].isin(movie_id)])
            else:
                return self
        elif type(movie_id) == str:
            return MovieCollection(self.df[self.df['imdb_title_id'] != movie_id])
        else:
            raise TypeError(f'Movie id only str or list, got {type(movie_id)}')
    
    
    def tags_similarity_score_collection(self, search_tags):
        self.df['tag_similarity_score'] = self.df['tags'].apply(
                self.__tags_similarity_score_for_movie, 
                args = (search_tags,)
                )
        weight_sim_score = 0.95
        self.df['general_score'] = (weight_sim_score*self.df['tag_similarity_score']) + (self.df['avg_vote']*0.1*(1-weight_sim_score))
         
    def sort(self, by: str, asc: bool):
        self.df.sort_values(by = by, axis = 0, inplace= True, ascending = asc)
  

class Talker(TextProcessor):
 
    def send_message(self, *messages: str) -> None:
        for msg in messages:
            self.telebot.send_message(self.chat_id, text=msg)
    
    def subset_of_movies_based_on_tags(self, tags: set) -> MovieCollection:
        self.movie_collection.tags_similarity_score_collection(tags)
        if self.testing: display(self.movie_collection.df.head(10))
        query_result = self.movie_collection.df[self.movie_collection.df['general_score'] > 0]
        if not query_result.empty:
            return MovieCollection(query_result)
        else:
            return None
    
    def __head_of_sorted_subset_of_movies(self, subset: MovieCollection, num_of_values: int) -> MovieCollection:
        if type(subset) == MovieCollection and type(num_of_values) == int:
            subset.sort(by = 'general_score', asc = False)
            return subset[:num_of_values]
        else:
            raise TypeError(f'''Wrong type in Talker.head_of_sorted_subset_of_movies method. 
                            Subset type: {type(subset)}
                            num_of_values type:{type(num_of_values)}''')
    
    def print_answer(self, subset):
        if subset:
            head_of_subset = self.__head_of_sorted_subset_of_movies(subset, 5)
            self.send_message(str(head_of_subset))
        else:
            self.send_message("No such movies in base")


class RegimeManager(Talker):
    
    def __init__(self, telebot: telebot.TeleBot) -> None:
        self.telebot = telebot
    
    def beginning(self, message: telebot.types.Message) -> None:
        self.chat_id = message.from_user.id
        keyboard = telebot.types.InlineKeyboardMarkup()  
        key_user_desc = telebot.types.InlineKeyboardButton(text='Recommend movies from description', 
                                                           callback_data='description') 
        keyboard.add(key_user_desc)
        key_user_fav = telebot.types.InlineKeyboardButton(text='Recommend movies like your favorite movies', 
                                                          callback_data='favorite') 
        keyboard.add(key_user_fav)
        self.telebot.send_message(self.chat_id, text='How you prefer to get recommendations', 
                                  reply_markup=keyboard)
        
    def returnBot(self, call, movie_collection, testing, telebot) -> None:
        if call.data == "favorite":
            self.send_message('Write a few of your favourite films, separated by semicolumn')
            return FavoriteRegime(movie_collection, testing, telebot, self.chat_id)
        elif call.data == "description":
            self.send_message('Write film themes you are interested in')
            return DescriptionRegime(movie_collection, testing, telebot, self.chat_id)
        else:
            raise Exception("Button error")
            

class FavoriteRegime(Talker):
    
    def __init__(self, movie_collection: MovieCollection, testing: bool, telebot: telebot.TeleBot, chat_id) -> None:
        self.movie_collection = movie_collection
        self.testing = testing
        self.telebot = telebot
        self.chat_id = chat_id
        self.clarification_set = []
        self.search_id_set = []
    
    
    def __favorite_tags_extraction(self, movie_names: str) -> set:
        search_tags = set()
        names = {name for name in movie_names.split(';')}
        for name in names:
            movies_with_this_title = self.movie_collection.search_by_title(name)
            if len(movies_with_this_title) == 1:
                search_tags.update(movies_with_this_title.get_tags())
                self.search_id_set.extend(movies_with_this_title.get_id(return_list = True))
            elif len(movies_with_this_title) > 1:
                self.clarification_set.append(movies_with_this_title)
            else:
                self.send_message(f"No movies named '{name.strip()}' in base")
            
        return search_tags
         
    
    def __multiple_films_with_one_name_handler(self):
        keyboard_mov = telebot.types.InlineKeyboardMarkup()
        for movie in self.clarification_set[0]:
            keyboard_mov.add(telebot.types.InlineKeyboardButton(text=f'{str(movie)}', 
                                                    callback_data=f'{movie["imdb_title_id"]}'))
        self.clarification_set.pop(0)
        self.send_message(f"Multiple movies named '{movie['original_title']}' are in base",
                                  "Please choose what movie exactly you are talking about")
        self.telebot.send_message(self.chat_id, text="Variants:", 
                                          reply_markup=keyboard_mov)
    
    def __multiple_films_with_one_name_check(self):
        if not self.clarification_set:
            self.answer()
        else:
            self.__multiple_films_with_one_name_handler()
    
    def __tags_injection(self, movie_id: str) -> None:
        movie = self.movie_collection.search_by_id(movie_id)
        self.tags.update(movie.get_tags())
        self.search_id_set.extend(movie.get_id(return_list = True))
    
    def add_tags_in_multiple_movies_with_same_name_situation(self, movie_id: str) -> None:
        self.__tags_injection(movie_id)
        self.__multiple_films_with_one_name_check()
        
    
    def message_processing(self, message: telebot.types.Message) -> None:
        self.tags = self.__favorite_tags_extraction(message.text)
        self.__multiple_films_with_one_name_check()
        
    def answer(self):
        if self.testing: print(f'Search tags: {self.tags}')
        subset = self.subset_of_movies_based_on_tags(self.tags)
        if subset:
            subset = subset.removed_by_id(self.search_id_set)
            if self.testing:print('search_id_set:', self.search_id_set)
            self.search_id_set.clear()
            self.print_answer(subset)


class DescriptionRegime(Talker):
    
    def __init__(self, movie_collection: MovieCollection, testing: bool, telebot: telebot.TeleBot, chat_id) -> None:
        self.movie_collection = movie_collection
        self.testing = testing
        self.telebot = telebot
        self.chat_id = chat_id
        
        
    def message_processing(self, message: telebot.types.Message) -> None:
        self.tags = self.description_tags_extraction(message.text)
        self.answer()
    
    def answer(self):
        if self.testing: print(f'Search tags: {self.tags}')
        subset = self.subset_of_movies_based_on_tags(self.tags)
        self.print_answer(subset)
             

