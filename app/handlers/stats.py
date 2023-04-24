from app.helpers.spotipy import SpotifyHelper
from app.models import Listen, Track
from sqlalchemy import func
from app import db

class StatsHandler:
    def total_listens(sp = None) -> int:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.filter_by(user_id = user.id).count()

    def total_minutes(sp = None) -> int:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.filter_by(user_id = user.id).count()

    def top_tracks(number, sp = None) -> list[str]:
        print(f"fetching top {number} tracks")
        number = 100 if number > 100 else number

        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()

        response = []
        top_tracks = Listen.query.with_entities(Listen.track_id, Track.name, func.count(Listen.track_id))\
                        .filter(Listen.user_id == user.id)\
                        .join(Track, Track.id==Listen.track_id)\
                        .group_by(Listen.track_id)\
                        .order_by( func.count(Listen.track_id).desc())\
                        .limit(number).all()
  
        for track in top_tracks:
            track_resp = get_track(track.track_id, sp)
            response.append({
                'name': track_resp.name,
                'image_url': track_resp.image_url,
                'listens': track[2]
            })    

        return response


def get_track(track_id, sp = None) -> Track | None:
    sp = SpotifyHelper() if sp is None else sp
    track: Track = Track.query.filter_by(id = track_id).one_or_none()
    if not track:
        return None
    elif track.from_spotify:
        return track
    else:   
        response = sp.track(track_id)
        track.from_spotify = True
        track.image_url = response['album']['images'][0]['url']
        track.preview_url = response['preview_url']
        db.session.commit()
    return track

