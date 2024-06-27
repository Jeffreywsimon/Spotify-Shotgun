from flask import Flask, render_template, jsonify, send_file, make_response, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import random
import logging
import os
import pandas as pd
import io
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

picFolder = os.path.join('static', 'pics')
app.config['UPLOAD_FOLDER'] = picFolder

# Replace these with your own Spotify Developer credentials
SPOTIPY_CLIENT_ID = os.getenv('CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('ClIENT_SECRET')


def authenticate_spotify():
    auth_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp


def get_random_albums(sp, num_albums=10):
    albums = []
    for _ in range(num_albums):
        # Search for albums with a query that ensures a larger set of results
        results = sp.search(q='', type='album', limit=1)
        total_albums = results['albums']['total']

        if total_albums > 0:
            offset = random.randint(0, total_albums - 1)
            results = sp.search(q='', type='album', limit=1, offset=offset)
            if results['albums']['items']:
                album = results['albums']['items'][0]
                album_info = {
                    'name': album['name'],
                    'artist': album['artists'][0]['name'],
                    'release_date': album['release_date'],
                    'total_tracks': album['total_tracks'],
                    'url': album['external_urls']['spotify'],
                    'image_url': album['images'][0]['url'] if album['images'] else None
                }
                albums.append(album_info)
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
        albums = get_random_albums(sp)
        return jsonify(albums)
    except Exception as e:
        app.logger.error(f"Error fetching albums: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/download-excel', methods=['GET'])
def download_excel():
    try:
        albums = get_random_albums(sp)
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
