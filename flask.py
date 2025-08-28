from flask import Flask, render_template, jsonify
import requests
import base64
import time
import random
import logging

app = Flask(__name__)
app.secret_key = "not slick"

# Setup logging to console with detailed format
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

CLIENT_ID = "nah ur not slick"
CLIENT_SECRET = "nah ur not slick"
REDIRECT_URI = "https://cruzy22k.pythonanywhere.com/callback"  # old shit
SCOPE = "user-read-currently-playing user-read-playback-state"

# Your 3 fallback tracks with titles, artists, and static image paths
fallback_tracks = [
    {
        "title": "PRIDE",
        "artist": "Kendrick Lamar",
        "image": "/static/kendrick.jpeg"
    },
    {
        "title": "Rich Baby Daddy",
        "artist": "Drake, SZA",
        "image": "/static/richbabydaddy.jpeg"
    },
    {
        "title": "WAIT FOR U",
        "artist": "Future, Tems",
        "image": "/static/waitforu.jpeg"
    }
]

spotify_tokens = {
    "access_token": None,
    "refresh_token": "nah ur not slick",
    "expires_at": 0
}

def get_auth_header():
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    logging.debug(f"Auth header: {auth_header}")
    return auth_header

def refresh_access_token():
    logging.info("refeshing")
    token_url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + get_auth_header(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": spotify_tokens.get("refresh_token")
    }
    try:
        resp = requests.post(token_url, headers=headers, data=data)
        resp.raise_for_status()
        token_data = resp.json()
        logging.debug(f"Token refresh response: {token_data}")
        spotify_tokens['access_token'] = token_data.get('access_token')
        spotify_tokens['expires_at'] = time.time() + token_data.get('expires_in', 3600)
        logging.info("refesh success")
    except Exception as e:
        logging.error(f"token failure shit this shouldnt happen: {e}")
        spotify_tokens['access_token'] = None

def get_fallback_track_data():
    track = random.choice(fallback_tracks)
    return {
        "track": f"{track['title']} - {track['artist']}",
        "progress_ms": random.randint(0, 180000),
        "duration_ms": 180000,  
        "album_art_url": track['image']
    }

@app.route('/spotify-now')
def spotify_now():
    logging.info("eeceived request to /spotify-now")

    # Refresh token if needed
    if (not spotify_tokens['access_token']) or (time.time() > spotify_tokens.get('expires_at', 0)):
        logging.info("No valid access token found or token expired, refreshing...")
        refresh_access_token()
        if not spotify_tokens['access_token']:
            logging.error("Failed to refresh access token, returning fallback song")
            return jsonify(get_fallback_track_data())

    headers = {
        "Authorization": "Bearer " + spotify_tokens['access_token']
    }

    try:
        r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
        logging.debug(f"Spotify API status code: {r.status_code}")

        if r.status_code == 204:
            logging.info("e 204")
            return jsonify(get_fallback_track_data())

        r.raise_for_status()

        data = r.json()
        logging.debug(f"spotify currently playing : {data}")

        if not data.get("is_playing", False):
            logging.info("Fall back song, error e spotify api down")
            return jsonify(get_fallback_track_data())

        item = data.get('item')
        if not item:
            logging.info("spotify is being shit")
            return jsonify(get_fallback_track_data())

        track_name = item.get('name')
        artists = ", ".join([artist['name'] for artist in item.get('artists', [])])
        progress_ms = data.get('progress_ms', 0)
        duration_ms = item.get('duration_ms', 0)
        album_images = item.get('album', {}).get('images', [])
        album_art_url = album_images[0]['url'] if album_images else get_fallback_track_data()['album_art_url']

        track_info = f"{track_name} - {artists}"
        logging.info(f"Returning current track with progress and album art: {track_info}")

        return jsonify({
            "track": track_info,
            "progress_ms": progress_ms,
            "duration_ms": duration_ms,
            "album_art_url": album_art_url
        })

    except Exception as e:
        logging.error(f"Error fetching currently playing track: {e}")
        return jsonify(get_fallback_track_data())

@app.route('/') # low taper fade business
def home():
    return render_template("mywebpage_index.html")

@app.route('/projects') # endless fields of yap
def projects(): 
    return render_template("projects.html")

@app.route('/forbidden') # lmao
def forbidden():
    return render_template("forbidden.html")

if __name__ == "__main__":
    app.run(debug=False)
