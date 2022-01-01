import sqlite3
from tabulate import tabulate

from pprint import pprint

database = sqlite3.connect('spotifydata.db')
cur = database.cursor()

def rankByListens(playlistName):
    tracks = cur.execute('''
    SELECT PlaylistTrack.trackName, PlaylistTrack.artistName, listens 
    FROM PlaylistTrack JOIN Playlist ON Playlist.playlistID == PlaylistTrack.playlistID 
        JOIN (SELECT artistName, trackName, Count(*) AS listens
        FROM HistoryFiltered
        GROUP BY trackName) trackListens ON trackListens.trackName == PlaylistTrack.trackName AND trackListens.artistName == PlaylistTrack.artistName
    WHERE Playlist.playlistName == '%s'
    ORDER BY listens DESC
    ''' % playlistName).fetchall()

    num = 0
    tableData = []
    for track in tracks:
        num += 1
        tableData.append([num, track[0], track[2], track[1]])
    return tabulate(tableData, headers=['#', 'Track Name', "Listens", 'Artist Name'])

if __name__ == "__main__":
    print(rankByListens('music paste 2021 2'))