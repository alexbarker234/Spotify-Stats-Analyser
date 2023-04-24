import os

from flask import jsonify, redirect, render_template, session
from app.helpers.spotipy import SpotifyHelper, UnauthorisedException

from app import app
from app.handlers.processer import ParseEndSongs
from app.handlers.stats import StatsHandler
from app.models import Listen


basedir = os.path.abspath(os.path.dirname(__file__))

@app.route('/index')
@app.route('/')
def indexPage():
    return render_template('index.html', title='Home', userdata=UserData())

@app.route('/stats')
def statsPage():
    print(StatsHandler.top_tracks())
    return render_template('stats.html', title='Stats', userdata=UserData())

@app.route('/upload')
def uploadPage():
    return render_template('upload.html', title='Upload', userdata=UserData())

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
    return redirect("/")


@app.route('/upload-file', methods=['POST'])
def upload():
    return ParseEndSongs()

@app.route('/total-listens')
def total_listens():
    try:
        sp = SpotifyHelper()
        user = sp.current_user()
        listens = Listen.query.filter_by(user_id = user.id).count()
        return jsonify(listens)
    except UnauthorisedException:
        return ""
    except Exception as e:
        return ""

class UserData:
    def __init__(self):
        try:
            sp = SpotifyHelper()
            
            payload = sp.me()
            self.authorized = True
            self.username = payload['display_name']
            self.image_url = payload['images'][0]['url'] if len(
                payload['images']) > 0 else None
            self.id = payload['id']
        except UnauthorisedException:
            print("unauthorised")
            pass