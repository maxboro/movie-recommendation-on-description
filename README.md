# movie-recommendation-on-description
Telegram bot that recommends movies based on movie description similarity (content-based recommender system)

Recommender work on film description similarity. Film description breaks down into tags.

There are two regime of work:
- In regime initiated by button "Write film themes you are interested in", user message breaks down into tags too, 
and films with higher tags similarity would be shown.
- In regime initiated by button "Write a few of your favourite films, separated by semicolumn", films mentioned by user
would be found in data, union of their tags would be user fo search. In case if in data there are a few movies with the same name 
user would be offered to choose from them with more film data provided.


