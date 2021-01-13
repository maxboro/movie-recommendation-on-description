import telebot
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
    
class MovieCollection :
    
    def __init__(self, df: pd.DataFrame):
        self.films = []
        for i in range(len(df)):
            self.films.append(Movie(df.iloc[i]))

class Bot:
    
    def __init__(self, code):
        self.tele_bot = telebot.TeleBot(code)
    