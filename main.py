import sqlite3
import os
import json
import re
from pprint import pprint

import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

from datetime import datetime
from datetime import timedelta
from tabulate import tabulate

above30Query = '''
    SELECT *
    FROM History
    WHERE msPlayed >=30000
    '''
daysBeingAnalysed = 0

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


database = sqlite3.connect('spotifydata.db')
cur = database.cursor()

def importData():
    # create table if it doesnt already exist
    cur.execute('''CREATE TABLE IF NOT EXISTS History (endTime datetime, artistName text, trackName text, msPlayed integer)''')

    #clear table
    cur.execute("DELETE FROM History")

    # parse json
    for subdir, dirs, files in os.walk("input"):
        for file in files:
            if (not file.endswith('.json')):
                continue
            f = open(os.path.join(subdir, file), encoding = "utf8")
            print('reading %s' % file)
            data = json.load(f)
            for song in data:
                values = ''
                for key in song:
                    if (key == 'msPlayed'):
                        values += "%s, " % str(song[key])
                    else:
                        values += "\"%s\", " % str(song[key]).replace('"', '""') # sqlite dislikes double quotes, double double quoting fixes that o.o
                values = values[:-2]  # remove last 2 chars
                query = "INSERT INTO History VALUES (%s)" % values
                #print(bcolors.WARNING + query + bcolors.ENDC)
                cur.execute(query)


    # remove duplicates and unknown tracks - probably a better way to do this
    cur.executescript(''' 
    CREATE TABLE IF NOT EXISTS HistoryTemp (endTime datetime, artistName text, trackName text, msPlayed integer);

    INSERT INTO HistoryTemp SELECT DISTINCT * FROM History WHERE trackName != "Unknown Track";

    DROP TABLE History;

    ALTER TABLE HistoryTemp
    RENAME TO History;
    ''')

    database.commit()

def analyse(duration):
    # check if data imported
    cur.execute(" SELECT name FROM sqlite_master WHERE type='table' AND name='History' ")
    if cur.fetchone() == None:
        print('data not imported')
        return

    global daysBeingAnalysed
    daysBeingAnalysed = cur.execute("SELECT COUNT(*) FROM (SELECT DISTINCT date(endTime) as date FROM History)").fetchone()[0]

    lastListen = cur.execute('''
    SELECT MAX(endTime)
    FROM History
    ''').fetchone()[0]

    lastListen = datetime.strptime(lastListen, "%Y-%m-%d %H:%M")

    if duration != '':
        days = int(re.findall('\d+',duration)[0])
        if re.search('\dm', duration):
            days *= 30
        elif re.search('\dy', duration):
            days *= 365
        elif not re.search('\dd', duration):
            print("that is not a valid duration")
            exit()

        endDate = lastListen - timedelta(days)
        
        print(endDate)

        global above30Query 
        above30Query= '''
            SELECT *
            FROM History
            WHERE msPlayed >= 30000 AND endTime > '%s'
            ''' % endDate

    outputFile = open("output/Statistics.txt", "w")
    totalMS = ''' 
    SELECT SUM(msPlayed) as totalTime
    FROM History;
    '''
    #print(cur.execute(totalMS).fetchone()[0])
    totalMinutes = int(cur.execute(totalMS).fetchone()[0] / 60000)
    outputFile.write("Minutes listened to Spotify: %s\n\n" % totalMinutes)

    topTracks = '''
    SELECT artistName, trackName, Count(*) AS Listens
    FROM (%s)
    GROUP BY trackName
    ORDER BY Listens DESC
    LIMIT 50
    ''' % above30Query
    outputFile.write("Your top 50 tracks are:\n\n")

    num = 0
    tableData = []
    for track in cur.execute(topTracks).fetchall():
        num += 1
        tableData.append([num,track[1],track[2],track[0]])
    outputFile.write(tabulate(tableData, headers=['#','Track Name', "Listens", 'Artist Name']))

    topArtists = '''
    SELECT artistName, Count(*) AS Listens
    FROM (%s)
    GROUP BY artistName
    ORDER BY Listens DESC
    LIMIT 50
    ''' % above30Query

    outputFile.write("\n\nYour top 50 artists are:\n\n")
    num = 0
    tableData = []
    for track in cur.execute(topArtists).fetchall():
        num += 1
        tableData.append([num,track[0],track[1]])
    outputFile.write(tabulate(tableData, headers=['#','Artist Name', "Listens"]))

    graphListens()
    graphTopArtistSongs()
    #graphArtistSongs('Maisie Peters')
    graphTopSongs()
    outputFile.close()


def graphListens():
    listensByHour = '''
    SELECT strftime('%%H',endTime) AS hour, COUNT(*) AS average
    FROM (%s)
    GROUP BY hour;
    ''' % above30Query
    hours = []
    values = []
    for row in cur.execute(listensByHour).fetchall():
        hours.append(datetime.strftime(datetime.strptime(row[0], "%H"),'%I%p'))
        values.append(row[1])
    #pprint(cur.execute(listensByHour).fetchall())
    plt.figure(figsize=(8,4))
    plt.bar(hours, values, width= 1)
    plt.xlabel('Hour')
    plt.ylabel('Total Listens')

    plt.xticks(rotation = 45)

    plt.savefig('output/Listens By Hour.png')
    plt.clf()

def graphTopArtistSongs():
    topArtists = '''
    SELECT artistName, Count(*) AS Listens
    FROM (%s)
    GROUP BY artistName
    ORDER BY Listens DESC
    LIMIT 5
    ''' % above30Query

    for artistName in cur.execute(topArtists).fetchall():   
        graphArtistSongs(artistName[0])

def graphArtistSongs(artistName):
    artistSongs = '''
    SELECT trackName
    FROM (%s)
    WHERE artistName="%s"
    GROUP BY trackName
    ORDER BY COUNT(*) DESC
    LIMIT 10
    '''% (above30Query, artistName)

    graphAccumulativeListens(cur.execute(artistSongs).fetchall())
    plt.savefig('output/Top 10 %s Songs.png' % artistName)
    plt.clf()
    
def graphTopSongs():
    songCount = '''
    SELECT trackName
    FROM (%s)
    GROUP BY trackName
    ORDER BY COUNT(*) DESC
    LIMIT 10
    '''% (above30Query)

    graphAccumulativeListens(cur.execute(songCount).fetchall())
    plt.savefig('output/Top 10 All Songs.png')
    plt.clf()


def graphAccumulativeListens(songList):
    getDates = '''
    SELECT DISTINCT date(endTime) as date
    FROM (%s)
    ''' % above30Query

    dates = []
    for date in cur.execute(getDates).fetchall():
        dates.append(date[0])

    plt.figure(figsize=(8,4))

    for songName in songList:   
        songListens = '''
        SELECT *
        FROM (%s)
        WHERE trackName = "%s"
        ''' % (above30Query, songName[0])

        songCounts = '''
        SELECT date AS endDate, COUNT(endTime)
        FROM (%s) LEFT JOIN (%s) ON date(endTime) = date
        GROUP BY endDate
        ''' % (getDates,songListens)

        values = []
        total = 0;
        for row in cur.execute(songCounts).fetchall():
            total += row[1]
            values.append(total)
        plt.plot(dates, values, '-', label=songName[0])
    
        plt.xticks(dates[::int(len(dates) / 5)]) 
        plt.xlabel('Date')
        plt.ylabel('Accumulative Listens')
        plt.legend()
    #plt.show()

val = input("import data? : ")
if (val == 'yes'): 
    importData()
duration = input("analyse for how long? : ")
analyse(duration)
