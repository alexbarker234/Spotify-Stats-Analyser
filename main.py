import sqlite3
import os
import json
import re
from pprint import pprint
import numpy as np
import math

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

from datetime import datetime
from datetime import timedelta
from tabulate import tabulate

from dotenv import load_dotenv

import requests
from io import BytesIO
from PIL import Image

import getAlbumImages

load_dotenv()


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
    if not os.path.exists('input'):
        os.mkdir('input')
    timezoneOffset = input("what is your UTC offset : ")

    # create table if it doesnt already exist
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS History (endTime datetime, artistName text, trackName text, msPlayed integer)''')

    # clear table
    cur.execute("DELETE FROM History")

    # parse json
    for subdir, dirs, files in os.walk("input"):
        for file in files:
            if (not file.endswith('.json')):
                continue
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
                        values += "\"%s\", " % str(song[key]
                                                   ).replace('"', '""')
                values = values[:-2]  # remove last 2 chars
                query = "INSERT INTO History VALUES (%s)" % values
                #print(bcolors.WARNING + query + bcolors.ENDC)
                cur.execute(query)

    timezoneOffset

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


def filter():
    # check if data imported
    cur.execute(
        " SELECT name FROM sqlite_master WHERE type='table' AND name='History' ")
    if cur.fetchone() == None:
        print('data not imported')
        return

    global daysBeingAnalysed
    daysBeingAnalysed = cur.execute(
        "SELECT COUNT(*) FROM (SELECT DISTINCT date(endTime) as date FROM History)").fetchone()[0]

    duration = input("analyse for how long? : ")

    lastListen = cur.execute('''
    SELECT MAX(endTime)
    FROM History
    ''').fetchone()[0]

    lastListen = datetime.strptime(lastListen, "%Y-%m-%d %H:%M:%S")

    above30Query = '''
    SELECT *
    FROM History
    WHERE msPlayed >=30000
    '''
    if duration != '':
        days = int(re.findall('\d+', duration)[0])
        if re.search('\dm', duration):
            days *= 30
        elif re.search('\dy', duration):
            days *= 365
        elif not re.search('\dd', duration):
            print("that is not a valid duration")
            exit()

        endDate = lastListen - timedelta(days)

        above30Query = '''
            SELECT *
            FROM History
            WHERE msPlayed >= 30000 AND endTime > '%s'
            ''' % endDate

    cur.executescript('''
        CREATE TABLE IF NOT EXISTS HistoryFiltered (endTime datetime, artistName text, trackName text, msPlayed integer);

        DELETE FROM HistoryFiltered;

        INSERT INTO HistoryFiltered %s;
    ''' % above30Query)


def analyse():
    artistGraphNum = input("how many artist graphs do you want? : ")
    if artistGraphNum == '':
        artistGraphNum = 10

    if not os.path.exists('output/Artist Accumulative'):
        os.makedirs('output/Artist Accumulative')
    outputFile = open("output/Statistics.txt", "w")

    totalMS = ''' 
    SELECT SUM(msPlayed) as totalTime
    FROM History;
    '''

    totalMinutes = int(cur.execute(totalMS).fetchone()[0] / 60000)
    outputFile.write("Minutes listened to Spotify: %s\n\n" % totalMinutes)

    outputFile.write(listeningSessions() + '\n\n')


    topTracks = '''
    SELECT artistName, trackName, Count(*) AS Listens
    FROM HistoryFiltered
    GROUP BY trackName
    ORDER BY Listens DESC
    LIMIT 50
    '''
    outputFile.write("Your top 50 tracks are:\n\n")

    num = 0
    tableData = []
    for track in cur.execute(topTracks).fetchall():
        num += 1
        tableData.append([num, track[1], track[2], track[0]])
    outputFile.write(tabulate(tableData, headers=[
                     '#', 'Track Name', "Listens", 'Artist Name']))

    topArtists = '''
    SELECT artistName, Count(*) AS Listens
    FROM HistoryFiltered
    GROUP BY artistName
    ORDER BY Listens DESC
    LIMIT 50
    '''

    outputFile.write("\n\nYour top 50 artists are:\n\n")
    num = 0
    tableData = []
    for track in cur.execute(topArtists).fetchall():
        num += 1
        tableData.append([num, track[0], track[1]])
    outputFile.write(tabulate(tableData, headers=[
                     '#', 'Artist Name', "Listens"]))

    graphListens()
    graphTopArtistSongs(artistGraphNum)
    monthlyTopTimeline()
    graphTopSongs()
    dailyMostListenedPieChart()
    outputFile.close()


def graphListens():
    listensByHour = '''
    SELECT strftime('%H',endTime) AS hour, COUNT(*) AS average
    FROM HistoryFiltered
    GROUP BY hour;
    '''
    hours = []
    values = []
    listensByHour = cur.execute(listensByHour).fetchall()
    for i in range(24):
        listens = [x for x in listensByHour if int(x[0]) == i]
        if listens == []:
            listens = 0
        else:
            listens = listens[0][1]

        hours.append(datetime.strftime(
            datetime.strptime(str(i), "%H"), '%I%p'))
        values.append(listens)
    plt.figure(figsize=(8, 4))
    plt.bar(hours, values, width=1)
    plt.xlabel('Hour')
    plt.ylabel('Total Listens')

    plt.xticks(rotation=45)

    plt.savefig('output/Listens By Hour.png')
    plt.close()


def graphTopArtistSongs(numToGraph=10):
    topArtists = '''
    SELECT artistName, Count(*) AS Listens
    FROM HistoryFiltered
    GROUP BY artistName
    ORDER BY Listens DESC
    LIMIT %s
    ''' % numToGraph

    for artistName in cur.execute(topArtists).fetchall():
        graphArtistSongs(artistName[0])


def graphArtistSongs(artistName):
    artistSongs = '''
    SELECT trackName
    FROM HistoryFiltered
    WHERE artistName="%s"
    GROUP BY trackName
    ORDER BY COUNT(*) DESC
    LIMIT 10
    ''' % artistName

    graphAccumulativeListens(cur.execute(artistSongs).fetchall())
    plt.title('Accumulative listens to ' + artistName)
    plt.savefig('output/Artist Accumulative/Top 10 %s Songs.png' %
                artistName.replace('/', ' '))
    plt.close()


def graphTopSongs():
    songCount = '''
    SELECT trackName
    FROM HistoryFiltered
    GROUP BY trackName
    ORDER BY COUNT(*) DESC
    LIMIT 10
    '''

    graphAccumulativeListens(cur.execute(songCount).fetchall())
    plt.title('Accumulative listens to your top 10 songs')
    plt.savefig('output/Top 10 All Songs.png')
    plt.close()


def graphAccumulativeListens(songList):
    getDates = '''
    SELECT DISTINCT date(endTime) as date
    FROM HistoryFiltered
    '''

    dates = []
    for date in cur.execute(getDates).fetchall():
        dates.append(date[0])

    plt.figure(figsize=(8, 4))

    for songName in songList:
        songListens = '''
        SELECT *
        FROM HistoryFiltered
        WHERE trackName = "%s"
        ''' % songName[0].replace('"', '""')

        songCounts = '''
        SELECT date AS endDate, COUNT(endTime)
        FROM (%s) LEFT JOIN (%s) ON date(endTime) = date
        GROUP BY endDate
        ''' % (getDates, songListens)

        values = []
        total = 0
        for row in cur.execute(songCounts).fetchall():
            total += row[1]
            values.append(total)
        plt.plot(dates, values, '-', label=songName[0])

        plt.xticks(dates[::math.ceil(len(dates) / 5)])
        plt.xlabel('Date')
        plt.ylabel('Accumulative Listens')
        plt.legend()


def dailyMostListenedPieChart():
    dailyTop = '''
    SELECT date, MAX(count) max, trackName
        FROM (
            SELECT date(endTime) date, COUNT(*) count, trackName
            FROM HistoryFiltered
            GROUP BY date(endTime), trackName)
    GROUP BY date
    '''

    numberOneCount = '''
    SELECT trackName, COUNT(*) timesMostListened 
    FROM (%s)    
    GROUP BY trackName
    ORDER BY timesMostListened DESC
    ''' % dailyTop

    labels = []
    sizes = []
    totalOther = 0
    totalArea = 0

    numberOneCount = cur.execute(numberOneCount).fetchall()

    for track in numberOneCount:
        totalArea += track[1]

    area = 0
    for track in numberOneCount:
        area += track[1]
        if track[1] / totalArea > 0.01:
            labels.append(track[0])
            sizes.append(track[1])
        else:
            totalOther += track[1]
    labels.append("Other")
    sizes.append(totalOther)

    def display(val):
        a = np.round(val/100 * totalArea, 0)
        label = str(int(a)) + ' days'  # + "\n" + '{0:.1f}'.format(val) + '%'
        return label

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.pie(sizes, labels=labels, autopct=display,
           shadow=True, startangle=90, pctdistance=0.8)
    # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.axis('equal')

    plt.title('Amount of times song was listened to the most in a day')
    plt.savefig('output/Daily Most Listened.png')
    plt.close()


def listeningSessions():
    sessionList = []
    songHistory = cur.execute("SELECT * FROM HistoryFiltered WHERE endTime > date('2021-12-24') AND endTime < date('2021-12-27')").fetchall()

    sessionStart = 0
    lastSongTime = 0

    for listen in songHistory:
        listenTime = datetime.strptime(listen[0], "%Y-%m-%d %H:%M:%S")
        if sessionStart == 0:
            sessionStart = listenTime
        if lastSongTime != 0:
            minsBetween = (listenTime - lastSongTime).total_seconds() / 60
            #print(str(listenTime) + ' ' + str(minsBetween))
            if minsBetween > 30:
                #print('appended ' + str(int((lastSongTime - sessionStart).total_seconds() / 60)))
                sessionList.append(
                    [int((lastSongTime - sessionStart).total_seconds() / 60), sessionStart, lastSongTime])
                sessionStart = 0
        lastSongTime = listenTime

    max = 0
    for i in range(len(sessionList)):
        if sessionList[i][0] > sessionList[max][0]:
            max = i

    day = sessionList[max][1].strftime("%d/%m/%Y")
    start = sessionList[max][1].strftime("%I:%M %p")
    end = sessionList[max][2].strftime("%d/%m/%Y %I:%M %p")
    length = str(int(sessionList[max][0] / 60)) + ' hours and ' + str(sessionList[max][0] % 60) + ' minutes'

    return "Your longest listening session was %s on %s and went from %s to %s" % (length, day, start, end)


def monthlyTopTimeline():
    monthlyTop = '''
    SELECT date, MAX(count) max, trackName, artistName
        FROM (
            SELECT strftime("%Y-%m", endTime) date, COUNT(*) count, trackName, artistName
            FROM HistoryFiltered
            GROUP BY date, trackName)
    GROUP BY date
    ORDER BY date ASC
    '''

    monthlyTop = cur.execute(monthlyTop).fetchall()

    dates = []
    topSongs = []
    levels = []
    images = []
    topMonth = 0
    # find the highest month listens
    for month in monthlyTop:
        if month[1] > topMonth:
            topMonth = month[1]

    # assign dates, songs, images, levels
    for month in monthlyTop:
        dates.append(month[0])
        topSongs.append(month[2] + "\n" + str(month[1]))
        levels.append((month[1] / topMonth) * 5)
        # images
        imageURL = getAlbumImages.findArtwork(month[2], month[3])
        if imageURL != '':
            response = requests.get(imageURL)
            images.append(Image.open(BytesIO(response.content)))
        else:
            images.append(Image.open('errorimage.png'))

    dates = [datetime.strptime(d, "%Y-%m") for d in dates]

    for i in range(len(levels)):
        if i % 2 == 0:
            levels[i] *= -1

    # create figure and plot a stem plot with the date
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_title("Top Monthly Song & Listens", pad=20)

    ax.vlines(dates, 0, levels, color="tab:red")  # The vertical stems.
    ax.plot(dates, np.zeros_like(dates), "-o",
            color="k", markerfacecolor="w")  # Baseline and markers on it.

    # annotate lines
    for d, l, r in zip(dates, levels, topSongs):
        ax.annotate(r, xy=(d, l),
                    xytext=(-3, np.sign(l)*3), textcoords="offset points",
                    horizontalalignment="center",
                    verticalalignment="bottom" if l > 0 else "top")

    imageHeights = []
    for level in levels:
        imageHeights.append(level + 2.1 * (-1 if level < 0 else 1))

    plotImages(dates, imageHeights, images, size=50, ax=ax)

    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")

    # remove y axis and spines
    ax.yaxis.set_visible(False)
    ax.spines[["left", "top", "right"]].set_visible(False)
    ax.margins(y=0.5)
    plt.savefig('output/Top Monthly Song & Listens.png')
    plt.close()

def plotImages(x, y, images, ax=None, size=100):
    if ax is None:
        ax = plt.gca()

    artists = []
    x, y = np.atleast_1d(x, y)
    for x0, y0, image in zip(x, y, images):
        width, height = image.size
        scale = min(size / width, size / height)
        image = np.array(image)

        im = OffsetImage(image, zoom=scale)

        ab = AnnotationBbox(im, (x0, y0), xycoords='data', frameon=False)
        artists.append(ax.add_artist(ab))

        ax.autoscale()
    return artists


val = input("import data? : ")
if (val == 'yes'):
    importData()
filter()
analyse()
