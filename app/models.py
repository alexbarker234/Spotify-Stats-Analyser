from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.String(120), primary_key=True)
    username = db.Column(db.String(120))

class Listen(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    track_id = db.Column(db.String(120), db.ForeignKey('track.id'))
    user_id = db.Column(db.String(120), db.ForeignKey('user.id'))

    end_time = db.Column(db.DateTime, index=True)
    ms_listened = db.Column(db.Integer)

class Track(db.Model):
    id = db.Column(db.String(120), primary_key=True)

    name = db.Column(db.String(120))
    preview_url = db.Column(db.String(), nullable=True)
    image_url = db.Column(db.String(), nullable=True)

class Artist(db.Model):
    id = db.Column(db.String(120), primary_key=True)

    name = db.Column(db.String(120), nullable=True)
    image_url = db.Column(db.String(), nullable=True)

class TrackArtist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    artist_id = db.Column(db.String(120), db.ForeignKey('artist.id'))
    track_id = db.Column(db.String(120), db.ForeignKey('track.id'))
