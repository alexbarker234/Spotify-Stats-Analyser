from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

load_dotenv()  

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv('spotifyClientID'), client_secret=os.getenv('spotifyClientSecret')))

artDict = {}

def findArtwork(trackName, artistName):
    print('finding artwork for %s by %s' % (trackName, artistName))

    if trackName in artDict: 
        print('already have image cached')
        return artDict[trackName]
       
    q = "artist:%s track:%s" % (artistName,trackName)
    results = sp.search(q, limit=10, type='track') 
    image = verifyArtistName(results,artistName)
    if not image is None:
        artDict[trackName] = image
        return image

    # sometimes the above query just hates life so do it again but different
    results = sp.search(trackName, limit=10, type='track') 
    image = verifyArtistName(results,artistName)
    if not image is None:
        artDict[trackName] = image
        return image
         
    return ''

def verifyArtistName(results, artistName):
    for item in results['tracks']['items']:  
        # check if the album artist is the artist, since the search returns a bunch of random albums that arent original
        for artist in item['album']['artists']: 
            if (artist['name'] == artistName):
                return item['album']['images'][0]['url']

    # just return first result if it cant verify :(
    if (len(results['tracks']['items']) > 0):
        return results['tracks']['items'][0]['album']['images'][0]['url']
    return None
