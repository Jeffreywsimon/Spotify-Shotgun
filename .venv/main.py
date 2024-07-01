import os
import base64
import json
from flask import Flask, render_template, jsonify, send_file, make_response,session
from dotenv import load_dotenv
from requests import post, get
import pandas as pd
import io
import random
import string
import xlsxwriter

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

picFolder = os.path.join('static', 'pics')
app.config['UPLOAD_FOLDER'] = picFolder

SPOTIPY_CLIENT_ID = os.getenv('CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('CLIENT_SECRET')

album_count = 0
albums_list = []  # List to store albums


def authenticate_spotify():
    auth_string = SPOTIPY_CLIENT_ID + ':' + SPOTIPY_CLIENT_SECRET
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

    url = 'https://accounts.spotify.com/api/token'
    headers = {
        'Authorization': 'Basic ' + auth_base64,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    sp = json_result['access_token']
    return sp


def get_auth_header(sp):
    return {'Authorization': 'Bearer ' + sp}


def get_random_albums(sp, limit=10):
    albums = []
    album_names = set()

    while len(albums) < limit:
        random_letter = random.choice(string.ascii_lowercase)
        random_offset = random.randint(1, 1000)

        url = 'https://api.spotify.com/v1/search'
        headers = get_auth_header(sp)
        query = f"?q={random_letter}&type=album&limit=1&offset={random_offset}"

        query_url = url + query
        result = get(query_url, headers=headers)
        json_result = json.loads(result.content)

        if 'albums' in json_result and 'items' in json_result['albums']:
            for item in json_result['albums']['items']:
                album_name = item['name']
                if album_name not in album_names:
                    album = {
                        'name': item['name'],
                        'artist': item['artists'][0]['name'],
                        'release_date': item['release_date'],
                        'total_tracks': item['total_tracks'],
                        'image_url': item['images'][0]['url'] if item['images'] else '',
                        'url': item['external_urls']['spotify']
                    }

                    albums.append(album)
                    album_names.add(album_name)

                if len(albums) >= limit:
                    break

    return albums


sp = authenticate_spotify()


@app.route('/')
def index():
    pic1 = os.path.join(app.config['UPLOAD_FOLDER'], '4b135b9f16b30caa386a32c6a64990c9.png')
    pic2 = os.path.join(app.config['UPLOAD_FOLDER'], 'soundtrap-C-2Wky-LT7k-unsplash.jpg')
    pic3 = os.path.join(app.config['UPLOAD_FOLDER'], 'Save.png')
    pic4 = os.path.join(app.config['UPLOAD_FOLDER'], 'Add.png')
    return render_template('index.html', user_image=pic1, user_image2=pic2, user_image3=pic3, user_image4=pic4)


@app.route('/random-albums', methods=['GET'])
def random_albums():
    try:
        new_albums = get_random_albums(sp, limit=10)
        return jsonify(new_albums)
    except Exception as e:
        app.logger.error(f"Error fetching albums: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download-albums', methods=['GET'])
def download_albums():
    try:
        albums_list = session.get('albums_list', [])
        if not albums_list:
            return jsonify({'error': 'No albums to download.'}), 400

        df = pd.DataFrame(albums_list)
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        df.to_excel(writer, index=False, sheet_name='Albums')
        writer.close()  # Correct method to save and close the writer
        output.seek(0)

        return send_file(output, download_name='albums.xlsx', as_attachment=True)
    except Exception as e:
        app.logger.error(f"Error downloading albums: {e}")
        return jsonify({'error': str(e)}), 500


@app.before_request
def make_session_permanent():
    session.permanent = True
    if 'albums_list' not in session:
        session['albums_list'] = []

@app.route('/store-albums', methods=['POST'])
def store_albums():
    try:
        new_albums = get_random_albums(sp, limit=10)
        albums_list = session.get('albums_list', [])
        albums_list.extend(new_albums)
        session['albums_list'] = albums_list  # Store updated list in session
        return jsonify({'success': True, 'albums': new_albums})
    except Exception as e:
        app.logger.error(f"Error storing albums: {e}")
        return jsonify({'error': str(e)}), 500






if __name__ == '__main__':
    app.run(debug=True)
