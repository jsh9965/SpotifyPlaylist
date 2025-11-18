from flask import Flask, render_template, redirect, session, request, url_for
import uuid
import os
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, SECRET_KEY
from spotify_client import SpotifyClient
import time

app = Flask(__name__)
app.secret_key = SECRET_KEY

def get_spotify_client():
    # Ensure each user/session gets its own cache file to avoid sharing tokens
    if 'spotify_cache_path' not in session:
        session['spotify_cache_path'] = f".spotify_cache_{uuid.uuid4().hex}"
    return SpotifyClient(
        SPOTIFY_CLIENT_ID,
        SPOTIFY_CLIENT_SECRET,
        SPOTIFY_REDIRECT_URI,
        cache_path=session['spotify_cache_path'],
        show_dialog=False
    )

@app.route('/')
def index():
    try:
        spotify_client = get_spotify_client()
        if 'spotify_token' not in session:
            auth_url = spotify_client.sp.auth_manager.get_authorize_url()
            return render_template('index.html', auth_url=auth_url)
        
        playlists = spotify_client.get_user_playlists()
        return render_template('index.html', playlists=playlists)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        session.clear()  # Clear the session if there's an error
        return redirect(url_for('index'))

@app.route('/callback')
def callback():
    try:
        spotify_client = get_spotify_client()
        code = request.args.get('code')
        if code:
            # Get the cached token
            token_info = spotify_client.sp.auth_manager.get_cached_token()
            # Mark user as signed in if token existed
            if token_info:
                session['spotify_token'] = True
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error in callback: {str(e)}")
        return redirect(url_for('index'))

@app.route('/one-hit-wonder-analysis', methods=['GET','POST'])
def one_hit_wonder_analysis():
    try:
        if 'spotify_token' not in session:
            print("No Spotify token in session.")
            return redirect(url_for('index'))
        if request.method == 'GET':
            print("Data needed for analysis.")
            return redirect(url_for('index'))
        
        playlist_id = request.form.get('playlist_id')
        spotify_client = get_spotify_client()
        
        one_hit_wonders = spotify_client.find_one_hit_wonders(playlist_id)
        if request.form.get('create_playlist'):
            playlist_url = spotify_client.create_playlist(one_hit_wonders, "My One Hit Wonders")
            return render_template('one_hit_wonder_results.html', tracks=one_hit_wonders, playlist_url=playlist_url)
        
        return render_template('one_hit_wonder_results.html', tracks=one_hit_wonders)
    except Exception as e:
        print(f"Error in one hit wonder results.html route: {str(e)}")
        session.clear()
        return redirect(url_for('index'))

@app.route('/vinyl-analysis', methods=['POST'])
def vinyl_analysis():
    try:
        if 'spotify_token' not in session:
            return redirect(url_for('index'))
        
        playlist_id = request.form.get('playlist_id')
        threshold = float(request.form.get('threshold', 0.5))  # Default to 50%
        spotify_client = get_spotify_client()
        
        # Pass minimum_album_size=4 to the analyze method
        vinyl_recommendations = spotify_client.analyze_albums_for_vinyl(
            playlist_id, 
            threshold=threshold, 
            minimum_album_size=4
        )
        return render_template('vinyl_results.html', recommendations=vinyl_recommendations)
    except Exception as e:
        print(f"Error in vinyl analysis route: {str(e)}")
        session.clear()
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    cache_path = session.pop('spotify_cache_path', None)
    if cache_path and os.path.exists(cache_path):
        os.remove(cache_path)
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)