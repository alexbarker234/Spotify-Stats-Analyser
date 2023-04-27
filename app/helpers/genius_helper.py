import re

from app.models import Track

from lyricsgenius import Genius, song
from config import Config

from difflib import SequenceMatcher

# This is very unreliable so will only work as a backup if spotify lyrics cant be found for a song
class GeniusHelper:
    def get_lyrics(spotify_track_id):
        track: Track = Track.query.filter(Track.id == spotify_track_id).one_or_none()
        if not track:
            return None
        
        genius = Genius(Config.GENIUS_TOKEN)
        genius_song: song.Song = genius.search_song(title=track.name, artist=track.artist_name)
        print(genius_song)
        # check how similar title & artist is
        if genius_song.artist != 'Genius' and\
            SequenceMatcher(None, genius_song.artist, track.artist_name).ratio() > 0.8 and\
            SequenceMatcher(None, genius_song.title, track.name).ratio() > 0.8:

            lyrics = genius_song.lyrics
            lyrics = re.sub(r'\[.*\]','', lyrics)

            # genius returning weird things on the start & end as its a scraper
            lyrics = re.sub(r'[0-9]Embed','', lyrics)
            lyrics = re.sub(r'You might also like','', lyrics)
            lyrics = re.sub(r'[0-9] Contributors.* Lyrics','', lyrics)
            
            lyrics = lyrics.split('\n')
            lyrics = list(filter(None, lyrics))
            return lyrics
        return None
        '''
        track_name = re.sub(r'[^a-zA-Z0-9 ]', '', track.name).lower().replace(' ', '-')
        artist_name = re.sub(r'[^a-zA-Z0-9 ]', '', track.name).lower().replace(' ', '-')
        link = f"https://genius.com/maisie-peters-{track_name}-lyrics"
        html = BeautifulSoup(requests.get(link).text, 'html.parser')
        html.find()
        '''

