import json
import sqlite3
import os

from pprint import pprint


database = sqlite3.connect('spotifydata.db')
cur = database.cursor()


def importData():
    if not os.path.exists('input'):
        os.mkdir('input')
    timezoneOffset = input("what is your UTC offset : ")

    # create table if it doesnt already exist
    cur.executescript('''
        CREATE TABLE IF NOT EXISTS History (endTime datetime, artistName text, trackName text, msPlayed integer);

        CREATE TABLE IF NOT EXISTS Playlist (playlistID integer, playlistName text);

        CREATE TABLE IF NOT EXISTS PlaylistTrack (playlistID integer, trackName text, artistName text, albumName text);
        ''')

    # clear table
    cur.executescript('''
        DELETE FROM History;
        DELETE FROM Playlist;
        DELETE FROM PlaylistTrack;
        ''')

    # parse json
    for subdir, dirs, files in os.walk("input"):
        for file in files:
            if 'StreamingHistory' in file:
                f = open(os.path.join(subdir, file), encoding="utf8")
                print('reading %s' % file)
                data = json.load(f)
                for song in data:
                    values = ''
                    for key in song:
                        if (key == 'msPlayed'):
                            values += "%s, " % str(song[key])
                        else:
                            # sqlite dislikes double quotes, double double quoting fixes that o.o
                            values += "\"%s\", " % str(song[key]).replace('"', '""')
                    values = values[:-2]  # remove last 2 chars
                    query = "INSERT INTO History VALUES (%s)" % values
                    #print(bcolors.WARNING + query + bcolors.ENDC)
                    cur.execute(query)
            elif 'Playlist' in file:
                f = open(os.path.join(subdir, file), encoding="utf8")
                print('reading %s' % file)
                data = json.load(f)
                platlistID = 0
                for playlist in data['playlists']:                 
                    playlistValues = "%s, \"%s\"" % (platlistID, playlist['name'])
                    cur.execute("INSERT INTO Playlist VALUES (%s)" % playlistValues)

                    for item in playlist['items']:
                        if (item['track'] is None): 
                            continue
                        values = "%s, \"%s\",\"%s\", \"%s\"" % (platlistID,
                            str(item['track']['trackName']).replace('"', '""'),
                            str(item['track']['artistName']).replace('"', '""'),
                            str(item['track']['albumName']).replace('"', '""'))
                        cur.execute("INSERT INTO PlaylistTrack VALUES (%s)" % values)
                        print()
                    platlistID += 1
    
    # remove duplicates and unknown tracks - probably a better way to do this
    cur.executescript(''' 
    CREATE TABLE IF NOT EXISTS HistoryTemp (endTime datetime, artistName text, trackName text, msPlayed integer);

    INSERT INTO HistoryTemp SELECT DISTINCT * FROM History WHERE trackName != "Unknown Track";

    UPDATE HistoryTemp SET endTime=DATETIME(endTime, '%s minutes');

    DROP TABLE History;

    ALTER TABLE HistoryTemp
    RENAME TO History;
    ''' % timezoneOffset * 60)

    database.commit()

if __name__ == "__main__":
    importData()