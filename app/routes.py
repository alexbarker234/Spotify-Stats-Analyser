import os
import sys

from flask import redirect, render_template, session
from app.helpers.spotipy import SpotifyHelper

from app import app
from app.handlers.processer import ParseEndSongs

basedir = os.path.abspath(os.path.dirname(__file__))


@app.route('/')
@app.route('/index')
def index():
    # , userdata=UserData()
    return render_template('index.html', title='Home', userdata={})


@app.route('/login')
def login():
    sp_oauth = SpotifyHelper.create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')


@app.route('/authorize')
def authorize():
    SpotifyHelper.authorise()
    return redirect("/index")


@app.route('/upload', methods=['POST'])
def upload():
    return ParseEndSongs()

'''
class UserData:
    def __init__(self):
        session['token_info'], self.authorized = get_token()
        session.modified = True
        print("Getting user data")
        if self.authorized:
            sp = spotipy.Spotify(auth=session.get(
                'token_info').get('access_token'))
            payload = sp.me()
            self.username = payload['display_name']
            self.image_url = payload['images'][0]['url'] if len(
                payload['images']) > 0 else None
            self.id = payload['id']
'''