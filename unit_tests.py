import unittest
from recommender import *


class Tests(unittest.TestCase):
    
    def setUp(self):
        self.df_test = pd.read_csv(
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
                    ).head(5)
    
    def test_description_tags_extraction(self):
        self.assertIn('cat', MixIn().description_tags_extraction('cats dogs reporters'))
        self.assertIn('reporter', MixIn().description_tags_extraction('cats dogs reporters'))
        self.assertIn('woman', MixIn().description_tags_extraction('women'))
        self.assertNotIn('.', MixIn().description_tags_extraction('cats .dogs, reporters'))
        self.assertNotIn(',', MixIn().description_tags_extraction('cats .dogs, reporters'))
    

unittest.main()

