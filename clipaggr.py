import requests
import json
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool
from pathlib import Path
import os 
from moviepy.editor import *

def getDownload(res):

    soup = BeautifulSoup(res.content, "html.parser")
    for link in soup.find_all('a'):
        for l in link.get('href').split('\n'):
            if "720.mp4" in l:
                return l

    return ""

if __name__ == '__main__':

    #get auth token
    print("GETTING AUTH TOKEN...")
    cid = "6yyf3r3ku7928nrc2cd61bz1w0p2rc"
    csec = "wc7mj2xmit6pf22r2kbxih74ynor57"
    url = "https://id.twitch.tv/oauth2/token?client_id={}&client_secret={}&grant_type=client_credentials".format(cid,csec)
    response = requests.post(url)
    auth = response.json()['access_token']
    headers = {"Authorization" : "Bearer {}".format(auth), "Client-Id" : cid}

    print("GETTING GAME ID...")
    response = requests.get("https://api.twitch.tv/helix/games/top", headers=headers)
    games = response.json()

    gameDict = []
    i = 0
    for game in games['data']:
        print(i, " ", game['name'])
        gameDict.append({"name" : game['name'], "id" : game['id']})
        i += 1

    gameIndex = input("ENTER GAME INDEX: ")
    gameId = gameDict[int(gameIndex)]["id"]
    gameName = gameDict[int(gameIndex)]["name"]

    today = datetime.today()
    todaySimple = today
    prev = datetime.today() - timedelta(days=1)

    today = today.astimezone().isoformat()
    prev = prev.astimezone().isoformat()

    print(today)
    print(prev)

    print("GETTING {} CLIPS...".format(gameName))
    response = requests.get("https://api.twitch.tv/helix/clips?game_id={}&started_at={}&ended_at={}".format(gameId, prev, today), headers=headers)
    clips = response.json()['data']

    ids = []

    for clip in clips:
        print(clip['id'])
        ids.append(clip['id'])

    pool = Pool(len(ids))

    print("GETTING DOWNLOAD LINKS...")

    futures = []
    for clip_id in ids:
        url = "https://clipr.xyz/{}".format(clip_id)
        futures.append(pool.apply_async(requests.get, [url]))

    vids = []
    for future in futures:
        link = getDownload(future.get())
        if link != "":
            vids.append(link)
    print("WRITING MP4 FILES...")
    
    try:
        os.mkdir('./clips', mode = 0o777)
    except FileExistsError:
        print("Directory exists")

    i = 0
    for vid in vids:
        r = requests.get(vid, allow_redirects=True)
        myfile = "./clips/temp_{}.mp4".format(i)
        open(myfile, 'w+b').write(r.content)
        print("CLIP AT {} FINISHED".format(vid))
        i += 1

    L =[]

    for root, dirs, files in os.walk("./clips"):

        #files.sort()
        for file in files:
            if os.path.splitext(file)[1] == '.mp4':
                filePath = os.path.join(root, file)
                video = VideoFileClip(filePath)
                L.append(video)

    final_clip = concatenate_videoclips(L)
    final_clip.to_videofile("final_{}.mp4".format(todaySimple), temp_audiofile='temp-audio.m4a', remove_temp=True, codec="libx264", audio_codec="aac")