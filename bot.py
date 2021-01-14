import telebot
import spacy
import numpy as np
import pandas as pd

df = pd.read_csv('movies_info.csv')

class Movie:
    
    def __init__(self, line: "Line of DataFrame"):
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
    
class MovieCollection :
    
    def __init__(self, df: pd.DataFrame):
        self.films = []
        for i in range(len(df)):
            self.films.append(Movie(df.iloc[i]))

class Bot:
    
    def __init__(self, code):
        self.tele_bot = telebot.TeleBot(code)
    