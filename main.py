import re

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import spotipy.util as util

import pickle

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


#-------------------------------SPOTIFY AND YOUTUBE API INFO---------------------------------
client_secrets_youtube = "" 

os.environ["SPOTIPY_CLIENT_ID"] = ""
os.environ["SPOTIPY_CLIENT_SECRET"] = ""

youtube_playlist_id = ""
spotify_playlist_id = ""
#--------------------------------------------------------------------------------------------


os.environ["SPOTIPY_REDIRECT_URI"] = 'http://localhost'

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

def get_authenticated_service():
    if os.path.exists("CREDENTIALS_PICKLE_FILE"):
        with open("CREDENTIALS_PICKLE_FILE", 'rb') as f:
            credentials = pickle.load(f)
    else:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_youtube, scopes)
        credentials = flow.run_console()
        with open("CREDENTIALS_PICKLE_FILE", 'wb') as f:
            pickle.dump(credentials, f)
    return googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials)

def getYoutubeTitles():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = client_secrets_youtube

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = get_authenticated_service()

    print()
    print("getting youtube titles...")
    print()

    songTitles = []

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=50,
        playlistId=youtube_playlist_id,
    )

    response = request.execute()

    for x in response["items"]:
        title = x["snippet"]["title"]
        songTitles.append(title)

    nextPageToken = response.get('nextPageToken')

    while(nextPageToken):
        request = youtube.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId=youtube_playlist_id,
            pageToken=nextPageToken
        )

        response = request.execute()

        for x in response["items"]:
            title = x["snippet"]["title"]
            songTitles.append(title)

        nextPageToken = response.get('nextPageToken')

    return songTitles

#--------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------#

def spotifyTrackIdsBy100(spotifyTrackIds):
    for i in range(0, len(spotifyTrackIds), 99):
        yield spotifyTrackIds[i:i + 99]

def findSong(songTitle, sp):
    songTitle = re.sub("[\(\[].*?[\)\]]", "", songTitle)

    print(songTitle)

    results = sp.search(q=songTitle, limit=1)
    if len(results['tracks']['items']) == 0:
        print('\033[41m' + "SONG NOT FOUND" + '\033[0m')
        return

    print('\033[43m' + "SONG FOUND" + '\033[0m')
    return results['tracks']['items'][0]['id']

def spotifyPart(songTitles):

    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())

    youtubeTrackIds = []

    spotifyPlaylist = sp.playlist(spotify_playlist_id)
    spotifyTrackIds = []
    for x in spotifyPlaylist["tracks"]["items"]:
        spotifyTrackIds.append(x["track"]["id"])

    for title in songTitles:
        songId = findSong(title, sp)

        print()

        if songId in spotifyTrackIds:
            print('\033[41m' + "NO NEW TRACKS" + '\033[0m')
            return

        if songId is not None:
            youtubeTrackIds.append(songId)

    if not youtubeTrackIds:
        print('\033[41m' + "NO NEW TRACKS" + '\033[0m')
        return

    userId = "11149983776"
    playlistId = spotify_playlist_id

    scope = 'playlist-modify-private'
    token = util.prompt_for_user_token(userId, scope)

    if(token):
        sp2 = spotipy.Spotify(auth=token)
        sp2.tracer = False

        trackIds = spotifyTrackIdsBy100(youtubeTrackIds)

        for trackIdsChunk in trackIds :
            sp2.user_playlist_add_tracks(userId, playlistId, trackIdsChunk)

        print('\033[43m' + str(len(youtubeTrackIds)) + " TRACKS ADDED OUT OF " + str(len(songTitles))+ '\033[0m')
    else:
        print('\033[41m' + "AUTHENTICATION FAILED" + '\033[0m')

#--------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------#
#--------------------------------------------------------------------------------------------------------------------#

def main():
    songTitles = getYoutubeTitles()
    print("adding spotify tracks to playlist...")
    print()
    spotifyPart(songTitles)

if __name__ == "__main__":
    main()
