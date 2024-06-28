import os
import base64
import json
from flask import Flask, render_template, jsonify, send_file, make_response
from dotenv import load_dotenv
from requests import post, get
import pandas as pd
import io
import random

load_dotenv()
app = Flask(__name__)

picFolder = os.path.join('static', 'pics')
app.config['UPLOAD_FOLDER'] = picFolder

# Replace these with your own Spotify Developer credentials
SPOTIPY_CLIENT_ID = os.getenv('CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('CLIENT_SECRET')

letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
random_letter = random.choice(letters)
print(random_letter)
random_offset=random.randint(1, 1000)
print(random_offset)
album_count=0


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


import random
import string

def get_random_albums(sp, limit=10):
    albums = []
    album_names = set()  # To keep track of unique album names

    while len(albums) < limit:
        random_letter = random.choice(string.ascii_lowercase)  # Select a random letter
        random_offset = random.randint(0, 1000)  # Randomize offset to reduce chance of duplicates

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
    return render_template('index.html', user_image=pic1, user_image2=pic2)


@app.route('/random-albums', methods=['GET'])
def random_albums():
    try:
        albums = get_random_albums(sp, limit=10)
        return jsonify(albums)
    except Exception as e:
        app.logger.error(f"Error fetching albums: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/download-excel', methods=['GET'])
def download_excel():
    try:
        letter = 'a'  # Example letter, you can make this dynamic
        albums = get_random_albums(sp, letter, limit=10)
        df = pd.DataFrame(albums)

        # Save the DataFrame to an Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Random Albums')

        output.seek(0)

        # Send the file to the client
        response = make_response(send_file(output, as_attachment=True, download_name='random_albums.xlsx',
                                           mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
        response.headers["Content-Disposition"] = "attachment; filename=random_albums.xlsx"
        return response
    except Exception as e:
        app.logger.error(f"Error creating Excel file: {e}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
