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
        self.collection_test = MovieCollection(self.df_test)
        self.desc_talker = DescriptionRegime(movie_collection = self.collection_test, testing = False, telebot = '', chat_id = '1')

    
    def test_text_proc_description_tags_extraction(self):
        self.assertIn('cat', TextProcessor().description_tags_extraction('cats 08 reporters  '))
        self.assertIn('reporter', TextProcessor().description_tags_extraction('cats 64 reporters'))
        self.assertIn('woman', TextProcessor().description_tags_extraction('women'))
        self.assertNotIn('.', TextProcessor().description_tags_extraction('cats .dogs, reporters'))
        self.assertNotIn(',', TextProcessor().description_tags_extraction('cats .dogs, reporters'))
    
    def test_text_proc_noun_chunks_filter(self):
        self.assertEqual(TextProcessor._TextProcessor__noun_chunks_filter({"his 'wife'", 'dog', 'as-salamu alaykum'}), {'as-salamu alaykum'})
    
    
    def test_mc_len__testing(self):
        self.assertEqual(len(self.collection_test), 5)
        self.assertEqual(len(self.collection_test), len(self.df_test))
    
    def test_mc_getitem_testing(self):
        self.assertEqual(len(self.collection_test) - 1, len(self.collection_test[1:]))
        
    def test_mc_tags_similarity_score_for_movie(self):
        self.assertEqual(self.collection_test._MovieCollection__tags_similarity_score_for_movie(
                search_tags = {'dog', 'cat', 'd', 'v'}, 
                movie_tags = {'dog', 'cat'}
                ), 0.5
            )
        
        self.assertEqual(self.collection_test._MovieCollection__tags_similarity_score_for_movie(
                search_tags = {'dog', 'cat'}, 
                movie_tags = {'dog', 'cat', 'd', 'v'}
                ), 1
            )
            
        self.assertEqual(self.collection_test._MovieCollection__tags_similarity_score_for_movie(
                search_tags = {}, 
                movie_tags = {'dog', 'cat', 'd', 'v'}
                ), 0
            )
    
    def test_talker_subset_of_movies_based_on_tags(self):
        self.assertEqual(self.desc_talker.subset_of_movies_based_on_tags(tags = set()), None)
        self.assertEqual(len(self.desc_talker.subset_of_movies_based_on_tags(tags = {'reporter'})), 1)
        self.assertEqual(len(self.desc_talker.subset_of_movies_based_on_tags(tags = {'true story'})), 1)
    
    
unittest.main()

