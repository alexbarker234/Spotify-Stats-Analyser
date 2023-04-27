from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.String(120), primary_key=True)

class Listen(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    track_id = db.Column(db.String(120))
    user_id = db.Column(db.String(120), db.ForeignKey('user.id', name="fk_user_id"))

    end_time = db.Column(db.DateTime, index=True)
    ms_played = db.Column(db.Integer)

class Track(db.Model):
    id = db.Column(db.String(120), primary_key=True)
    name = db.Column(db.String(120))
    # this is bad practice but endsong doesnt have artist id
    artist_name = db.Column(db.String(120)) 

    from_spotify = db.Column(db.Boolean(), default=False)
    preview_url = db.Column(db.String(), nullable=True)
    image_url = db.Column(db.String(), nullable=True)

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(120), nullable=True)
    image_url = db.Column(db.String(), nullable=True)

class TrackArtist(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    artist_id = db.Column(db.String(120), db.ForeignKey('artist.id', name="fk_artist_id"))
    track_id = db.Column(db.String(120), db.ForeignKey('track.id', name="fk_track_id"))
