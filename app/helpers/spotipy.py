import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import request, url_for, session
import time
from config import Config

class UnauthorisedException(Exception):
    "Raised when user is not authorised"
    pass

class SpotifyHelper(spotipy.Spotify):
    '''
    Creates a wrapper class of spotipy.Spotify that checks if the user is logged in first 

    Also makes some methods return an object rather than dictionary (wack..?)

    This implementation is questionable
    '''
    def __init__(self):
        session['token_info'], authorized = self.get_token()
        session.modified = True
        if not authorized:
            raise UnauthorisedException("The user is not logged in")
        super(SpotifyHelper, self).__init__(auth=session.get('token_info').get('access_token'))

    def get_token(self):
        '''
        Checks to see if token is valid and gets a new token if not
        '''
        token_valid = False
        token_info = session.get("token_info", {})

        # Checking if the session already has a token stored
        if not (session.get('token_info', False)):
            token_valid = False
            return token_info, token_valid

        # Checking if token has expired
        now = int(time.time())
        is_token_expired = session.get('token_info').get('expires_at') - now < 60

        # Refreshing token if it has expired
        if (is_token_expired):
            sp_oauth = self.create_spotify_oauth()
            token_info = sp_oauth.refresh_access_token(
                session.get('token_info').get('refresh_token'))

        token_valid = True
        return token_info, token_valid
    
    @staticmethod
    def create_spotify_oauth():
        return SpotifyOAuth(
            client_id=Config.SPOTIPY_CLIENT_ID,
            client_secret=Config.SPOTIPY_CLIENT_SECRET,
            redirect_uri=url_for('authorize', _external=True),
            scope="user-library-read user-top-read playlist-read-private user-read-private")
    
    @staticmethod
    def authorise():
        sp_oauth = SpotifyHelper.create_spotify_oauth()
        session.clear()
        code = request.args.get('code')
        token_info = sp_oauth.get_access_token(code)
        session["token_info"] = token_info

    def current_user(self):
        return SpotifyUser(super().current_user())


# Track Model

class SpotifyTrack:
    def __init__(self, json_dict: dict):
        self.country: str = json_dict.get("country")

# User Model
class SpotifyUser:
    def __init__(self, json_dict: dict):
        self.country: str = json_dict.get("country")
        self.display_name: str = json_dict.get("display_name")
        self.email: str = json_dict.get("email")
        self.explicit_content = ExplicitContent(json_dict.get("explicit_content"))
        self.external_urls = ExternalUrls(json_dict.get("external_urls"))
        self.followers = Followers(json_dict.get("followers"))
        self.href: str = json_dict.get("href")
        self.id: str = json_dict.get("id")
        self.image = Image(json_dict.get("images")[0])
        self.product: str = json_dict.get("product")
        self.type: str = json_dict.get("type")
        self.uri: str = json_dict.get("uri")


class ExplicitContent:
    def __init__(self, json_dict: dict):
        self.filter_enabled: bool = json_dict.get("followers")
        self.filter_locked: bool = json_dict.get("followers")


class ExternalUrls:
    def __init__(self, json_dict: dict):
        self.spotify: str = json_dict.get("spotify")


class Followers:
    def __init__(self, json_dict: dict):
        self.href: None = json_dict.get("href")
        self.total: int = json_dict.get("total")


class Image:
    def __init__(self, json_dict: dict):
        self.url: str = json_dict.get("url")
        self.height: int = json_dict.get("height")
        self.width: int = json_dict.get("width")
