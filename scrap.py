import requests        
from bs4 import BeautifulSoup
from lxml import etree
import json
import re

import multiprocessing as mp
import time
import sys
import os
import operator

from wordcloud import WordCloud
import matplotlib.pyplot as plt
from nltk.corpus import stopwords

SONG_MAIN_URL = "https://genius.com{}"
ARTIST_MAIN_URL = "https://genius.com/artists/{}"
SONGS_API_URL = 'https://genius.com/api/artists/{}/songs?page={}'

lock = mp.Lock()

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
   text = soup.find('div', {'data-lyrics-container': 'true'}).decode_contents().strip()
   raw_lyrics = re.sub(r"\<[^\>]+\>", ' ', text)
   raw_lyrics = re.sub(r"\([^\)]+\)", '', raw_lyrics)
   lyrics = re.sub(r"\[[^\]]+\]", '', raw_lyrics)

   return lyrics

def count_words(path, bow):
   print(f"Get {SONG_MAIN_URL.format(path)}")
   
   try:
      lyrics = get_lyrics(path)
   except:
      print("An error occurred")

   for word in lyrics.split(" "):
      word = word.lower()
      word = re.sub(r'[\W_]+', '', word)
      
      if word in stopwords.words():
         continue
      
      with lock:
         if word in bow.keys():
            bow[word]+=1
         else:
            bow[word]=1

start = time.time()

if(len(sys.argv) <= 1):
   print("No input found...")
   exit()

artist = "-".join(sys.argv[1:])
artist_main_url = ARTIST_MAIN_URL.format(artist)
                         
print(f'Get {artist_main_url}')
artist_id = get_artist_id(artist_main_url)

print('Get songs path... (it may take a while)')
songs_path = get_songs_path(artist_id)

bow = mp.Manager().dict(lock=True)
pool = mp.Pool(mp.cpu_count())

pool.starmap(count_words,[(path, bow) for path in songs_path])

pool.close()
pool.join()

os.makedirs("./output", exist_ok=True)

wordcloud = WordCloud(width = 800, height = 800,
                background_color ='white',
                min_font_size = 10).fit_words(bow)

plt.figure(figsize = (8, 8), facecolor = None)
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout(pad = 0)
 
plt.savefig(f"./output/{artist}.png")

end = time.time()
print(end-start)