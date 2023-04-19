from flask import render_template, request, url_for, session, redirect, jsonify
import time

from app import app, db

from datetime import datetime


from config import Config

import spotipy
from spotipy.oauth2 import SpotifyOAuth

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home', userdata=UserData())

@app.route('/login')
def login():    
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/logout')
def logout():    
    for key in list(session.keys()):
        session.pop(key)
    return redirect('/')

@app.route('/authorize')
def authorize():
    sp_oauth = create_spotify_oauth()
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session["token_info"] = token_info
    return redirect("/index")

# Checks to see if token is valid and gets a new token if not
def get_token():
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
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid

def create_spotify_oauth():
    return SpotifyOAuth(
            client_id = Config.SPOTIPY_CLIENT_ID,
            client_secret = Config.SPOTIPY_CLIENT_SECRET,
            redirect_uri = url_for('authorize', _external=True),
            scope = "user-library-read user-top-read playlist-read-private")

class UserData:
    def __init__(self):
        session['token_info'], self.authorized = get_token()
        session.modified = True
        if self.authorized:
            sp = spotipy.Spotify(auth=session.get('token_info').get('access_token'))
            payload = sp.me()
            self.username = payload['display_name']     
            self.image_url = payload['images'][0]['url'] if len(payload['images']) > 0 else None
            self.id = payload['id']
