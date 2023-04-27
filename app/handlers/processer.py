import datetime
import json
from flask import request
from app import db
import traceback
import sqlalchemy as sa
from sqlalchemy.dialects.sqlite import insert
from colorama import Fore
from abc import ABC, abstractmethod
from app.models import Listen, User, Track, Artist

from app.helpers.spotipy import SpotifyHelper, SpotifyUser

# obj to string: json.loads(json.dumps(user, default=lambda o: o.__dict__))


def ParseEndSongs():
    f = request.files.get('file')
    print(f"parsing file: {f.filename}")
    try:
        sp = SpotifyHelper()
        if not sp:
            return "not signed in", 500

        endsongs: list[_EndSong] = json.load(f, object_hook=_EndSong.from_json)

        print("finished parsing json")

        if len(endsongs) == 0:
            return "empty", 500

        user = sp.current_user()

        db_user = User.query.filter_by(id=user.id)
        if not db_user:
            db_user = User(id=user.id)
            db.session.add(db_user)
        i = 0

        tracks = {}

        for endsong in endsongs:
            if i % 100 == 0:
                print(f'{i}/{len(endsongs)}', end='\r')
            i += 1
            # skip bad entries (local files, errors)
            if not endsong or not endsong.track_id:
                continue
            # print(endsong)
            # if the user uploads the wrong files
            if endsong.user_id != user.id:
                continue

            # spotify only counts listens as above 30 seconds
            if endsong.ms_played < 30000:
                continue

            # add track to dict for inserting
            tracks[endsong.track_id] = {'id':endsong.track_id, 'name':endsong.track_name, 'artist_name':endsong.artist_name}

            # insert the listen
            listen = Listen(user_id=user.id,
                            track_id=endsong.track_id,
                            end_time=datetime.datetime.fromisoformat(
                                endsong.end_time[:-1]),
                            ms_played=int(endsong.ms_played))
            db.session.add(listen)

        # add tracks if they dont exist
        track_list = list(tracks.values())
        batch_size = 999 # sqlite has a 999 limit
        for i in range(0, len(track_list), batch_size):
            batch = track_list[i:i+batch_size]  # get the next batch of data
            stmt = insert(Track).values(batch).on_conflict_do_nothing(index_elements=['id'])
            db.session.execute(stmt)

        # delete duplicates - if file is uploaded multiple times

        # get the maximum id by end time
        inner_q = db.session.query(sa.func.max(Listen.id)).filter_by(
            user_id=user.id).group_by(Listen.end_time)
        # get the rows that arent in that & delete
        q = Listen.query.filter(~Listen.id.in_(inner_q))
        for domain in q:
            db.session.delete(domain)

        db.session.commit()
        print(f"finished parsing file: {f.filename}")
        return json.dumps({'success': True}), 200, {'ContentType': 'application/json'}
    except json.JSONDecodeError:
        return "Invalid JSON", 500
    except Exception as e:
        print(f"{Fore.RED}ERROR:")
        traceback.print_exc()
        print(Fore.RESET)
        return "An error occured", 500


class _JsonObj(ABC):
    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        return self.__str__()

    @abstractmethod
    def from_json(self):
        pass


class _EndSong(_JsonObj):
    def __init__(self, ts, username, ms_played, spotify_track_uri, master_metadata_track_name, master_metadata_album_artist_name):
        self.end_time = ts
        self.user_id = username
        self.ms_played = ms_played
        # take only the ID from the URI eg spotify:track:xxxxxxxxxxxxxxxxxxxxxx -> xxxxxxxxxxxxxxxxxxxxxx
        self.track_id = spotify_track_uri[14:] if spotify_track_uri else None
        self.track_name = master_metadata_track_name
        self.artist_name = master_metadata_album_artist_name

    staticmethod

    def from_json(json_dct):
        try:
            return _EndSong(json_dct['ts'],
                            json_dct['username'],
                            json_dct['ms_played'],
                            json_dct['spotify_track_uri'],
                            json_dct['master_metadata_track_name'],
                            json_dct['master_metadata_album_artist_name'])
        except Exception as e:
            print(f"AN ERROR OCCURED: {e}\nPAYLOAD:\n{json_dct}")
            return None
