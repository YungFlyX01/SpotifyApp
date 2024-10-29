import requests
from base64 import b64encode
import pandas as pd
from flask import Flask, render_template, request, send_file, session
from io import StringIO
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

def get_token():
    auth_token = b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode("utf-8")
    url = 'https://accounts.spotify.com/api/token'
    headers = {
        "Authorization": f"Basic {auth_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials"
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    token = response.json()
    return token['access_token']

@app.route('/', methods=['GET', 'POST'])
def index():
    artist_image_url = None
    track_list = []
    if request.method == 'POST':
        artist_name = request.form['artist_name']
        session['artist_name'] = artist_name  # Store artist name in session
        token = get_token()
        headers = {
            "Authorization": f"Bearer {token}"
        }
        url = 'https://api.spotify.com/v1/search'
        params = {
            "q": artist_name,
            "type": "artist"
        }
        music_response = requests.get(url, headers=headers, params=params)
        music_response.raise_for_status()
        data = music_response.json()["artists"]["items"]
        
        if data:
            artist_image_url = data[0]['images'][0]['url']
            artist_id = data[0]['id']
            track_url = f'https://api.spotify.com/v1/artists/{artist_id}/top-tracks?market=US'
            track_response = requests.get(track_url, headers=headers)
            track_response.raise_for_status()
            tracks_data = track_response.json()["tracks"]

            for track in tracks_data:
                track_name = track['name']
                image_url = track['album']['images'][0]['url']
                music_url = track['external_urls']['spotify']

                track_list.append({
                    "track": track_name,
                    "image_url": image_url,
                    "music_url": music_url,
                })

            session['track_list'] = track_list  # Store track_list in session

    return render_template('index.html', artist_image_url=artist_image_url, track_list=track_list)

@app.route('/download')
def download():
    artist_name = session.get('artist_name', 'unknown_artist')
    track_list = session.get('track_list', [])
    filename = f"{artist_name}_data.csv"

    df = pd.DataFrame(track_list)
    csv_data = StringIO()
    df.to_csv(csv_data, index=False)
    csv_data.seek(0)
    
    return send_file(csv_data, as_attachment=True, download_name=filename, mimetype='text/csv')

if __name__ == '__main__':
    app.run(debug=True)
