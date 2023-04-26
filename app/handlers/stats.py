import math
from app.helpers.spotipy import SpotifyHelper
from app.models import Listen, Track
from sqlalchemy import func
from app import db


class StatsHandler:
    def total_listens(sp=None) -> int:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.filter_by(user_id=user.id).count()

    def total_minutes(sp=None) -> int:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.filter_by(user_id=user.id).count()

    def top_tracks(number, sp=None) -> list[str]:
        print(f"fetching top {number} tracks")
        number = 100 if number > 100 else number

        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()

        response = []
        top_tracks = Listen.query.with_entities(Listen.track_id, Track.name, func.count(Listen.track_id))\
            .filter(Listen.user_id == user.id)\
            .join(Track, Track.id == Listen.track_id)\
            .group_by(Listen.track_id)\
            .order_by(func.count(Listen.track_id).desc())\
            .limit(number).all()

        for track in top_tracks:
            # print(track)
            track_resp = get_track(track.track_id, sp)
            response.append({
                'id': track_resp.id,
                'name': track_resp.name,
                'image_url': track_resp.image_url,
                'listens': track[2]
            })

        return response

    def listens_graph(track_id, sp=None):
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        response = []
        print(f"fetching daily listens for {track_id}")
        listens = Listen.query.with_entities(Listen.track_id, func.strftime("%Y-%m-%d", Listen.end_time), func.count(Listen.track_id))\
                        .filter(Listen.user_id == user.id, Listen.track_id == track_id)\
                        .join(Track, Track.id == Listen.track_id)\
                        .group_by(func.strftime("%Y-%m-%d", Listen.end_time))\
                        .order_by((Listen.end_time).asc()).all()
        for listen in listens:
            response.append(
                {'day': listen[1], 'listens': listen[2]})
        return response

    def track_data(track_id, sp=None):
        print(f"fetching track details for {track_id}")
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()

        track: Track = Track.query.filter(Track.id == track_id).one_or_none()
        if not track:
            return ""

        listens: list[Listen] = Listen.query\
                        .filter(Listen.user_id == user.id, Listen.track_id == track_id).all()
        minutes_listend = math.floor(sum(c.ms_played for c in listens) / 60000)

        return {
            'name': track.name,
            'imageUrl': track.image_url,
            'totalListens': len(listens),
            'totalMinutes': minutes_listend
        }


def get_track(track_id, sp=None) -> Track | None:
    sp = SpotifyHelper() if sp is None else sp
    track: Track = Track.query.filter_by(id=track_id).one_or_none()
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
