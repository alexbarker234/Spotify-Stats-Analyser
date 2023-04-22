from app.helpers.spotipy import SpotifyHelper
from app.models import Listen

def total_listens(sp = None) -> int:
    if sp is None:
        sp = SpotifyHelper()
    user = sp.current_user()
    return Listen.query.filter_by(user_id = user.id).count()

def total_minutes(sp = None) -> int:
    if sp is None:
        sp = SpotifyHelper()
    user = sp.current_user()
    return Listen.query.filter_by(user_id = user.id).count()
