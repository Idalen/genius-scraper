import requests        
from bs4 import BeautifulSoup
from lxml import etree
import json
import re

import time
import sys
import os

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords

SONG_MAIN_URL = "https://genius.com{}"
ARTIST_MAIN_URL = "https://genius.com/artists/{}"
SONGS_API_URL = 'https://genius.com/api/artists/{}/songs?page={}'

def get_artist_id(url):
   source_data = requests.get(url).content
   soup = BeautifulSoup(source_data, 'html.parser')
   artist_id = soup.find('link', rel="alternate")['href'].split('/')[-1]
   return artist_id

def get_songs_path(artist_id):
   page = 1
   song_paths = []
   while page:
      res = json.loads(requests.get(SONGS_API_URL.format(artist_id, page)).content)['response']
      for song in res['songs']:
         if not song['instrumental'] and song['lyrics_state'] == 'complete':   
            song_paths.append(song['path'])
      page = res['next_page']

   return song_paths

def get_lyrics(path):
   source_data = requests.get(SONG_MAIN_URL.format(path)).content
   soup = BeautifulSoup(source_data, 'html.parser')
   text = soup.find('div', {'data-lyrics-container': 'true'}).decode_contents().strip().replace("<br/>", ' ')
   lyrics = re.sub('\[*.\]', '', text)

   return lyrics

artist = " ".join(sys.argv[1:])
artist_main_url = ARTIST_MAIN_URL.format(artist)
                         
print(f'Get {artist_main_url}')
artist_id = get_artist_id(artist_main_url)

print('Get songs path... (it may take a while)')
songs_path = get_songs_path(artist_id)


for path in songs_path:
   print(f"Get {SONG_MAIN_URL.format(path)}")
   lyrics = get_lyrics(path)

   bow = {}
   for word in lyrics.split(" "):
      word = word.lower()
      word = re.sub(r'[\W_]+', '', word)
      
      if word in stopwords.words():
         continue
      
      if word in bow.keys():
         bow[word]+=1
      else:
         bow[word]=1
      
os.makedirs("./output", exist_ok=True)

wordcloud = WordCloud(width = 800, height = 800,
                background_color ='white',
                min_font_size = 10).fit_words(bow)

plt.figure(figsize = (8, 8), facecolor = None)
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout(pad = 0)
 
plt.savefig(f"./output/{artist}.png")