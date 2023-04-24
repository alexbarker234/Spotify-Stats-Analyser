from app.helpers.spotipy import SpotifyHelper
from app.models import Listen
from sqlalchemy import func

class StatsHandler:
    def total_listens(sp = None) -> int:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.filter_by(user_id = user.id).count()

    def total_minutes(sp = None) -> int:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.filter_by(user_id = user.id).count()

    def top_tracks(sp = None) -> list[str]:
        sp = SpotifyHelper() if sp is None else sp
        user = sp.current_user()
        return Listen.query.with_entities(Listen.track_id, func.count(Listen.track_id))\
                .filter_by(user_id = user.id)\
                .group_by(Listen.track_id)\
                .order_by( func.count(Listen.track_id).desc())\
                .limit(50).all()

class Track:
    def __init__(self) -> None:
        pass