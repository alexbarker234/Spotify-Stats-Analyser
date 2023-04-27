import os

from flask import abort, jsonify, redirect, render_template, session
from app.helpers.genius_helper import GeniusHelper
from app.helpers.spotipy import SpotifyHelper, UnauthorisedException

from app import app, db
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
    return render_template('stats.html', title='Stats', userdata=UserData())

@app.route('/stats/track/<track_id>')
def statsTrackPage(track_id):
    return render_template('statsTrack.html', title='Stats', userdata=UserData())

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
        return jsonify(StatsHandler.total_listens())
    except UnauthorisedException:
        return ""
    except Exception as e:
        return ""

@app.route('/top-tracks/<number>')
def top_tracks(number):
    try:
        return jsonify(StatsHandler.top_tracks(int(number)))
    except UnauthorisedException:
        return ""
    except Exception as e:
        return ""

@app.route('/listens-graph/<track_id>')
def listens_graph(track_id):
    try:
        return jsonify(StatsHandler.listens_graph(track_id))
    except UnauthorisedException:
        return ""
    except Exception as e:
        return ""

@app.route('/track-data/<track_id>')
def track_data(track_id):
    try:
        return jsonify(StatsHandler.track_data(track_id))
    except UnauthorisedException:
        return ""
    except Exception as e:
        return ""

@app.route('/genius-lyrics/<track_id>')
def genius_lyrics(track_id):
    result = GeniusHelper.get_lyrics(track_id)
    if result == None:
        return abort(404)
    return jsonify(result)

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