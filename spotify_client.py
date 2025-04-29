import spotipy
from spotipy.oauth2 import SpotifyOAuth
from collections import defaultdict

class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.scope = 'playlist-read-private playlist-modify-public playlist-modify-private'
        
        # Create cache handler with a unique name
        cache_handler = spotipy.cache_handler.CacheFileHandler(cache_path=".spotify_cache")
        
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.scope,
            cache_handler=cache_handler,
            show_dialog=True  # This forces the user to approve the app every time
        )
        
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

    def get_user_playlists(self):
        results = self.sp.current_user_playlists()
        playlists = []
        while results:
            playlists.extend(results['items'])
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        return playlists

    def get_playlist_tracks(self, playlist_id):
        results = self.sp.playlist_tracks(playlist_id)
        tracks = []
        while results:
            tracks.extend(results['items'])
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        return tracks

    def find_one_hit_wonders(self, playlist_id):
        tracks = self.get_playlist_tracks(playlist_id)
        artist_tracks = defaultdict(list)

        for track in tracks:
            if track['track']:
                artist_id = track['track']['artists'][0]['id']
                artist_tracks[artist_id].append({
                    'name': track['track']['name'],
                    'uri': track['track']['uri'],
                    'artist': track['track']['artists'][0]['name']
                })

        one_hit_wonders = []
        for artist_id, tracks in artist_tracks.items():
            if len(tracks) == 1:
                one_hit_wonders.append(tracks[0])

        return one_hit_wonders

    def create_playlist(self, tracks, playlist_name):
        user_id = self.sp.current_user()['id']
        playlist = self.sp.user_playlist_create(
            user_id,
            playlist_name,
            description="One Hit Wonders playlist created by Spotify One Hits app"
        )
        
        track_uris = [track['uri'] for track in tracks]
        self.sp.playlist_add_items(playlist['id'], track_uris)
        return playlist['external_urls']['spotify']
    
    def get_album_tracks(self, album_id):
        """Get all tracks from an album."""
        results = self.sp.album_tracks(album_id)
        tracks = []
        while results:
            tracks.extend(results['items'])
            if results['next']:
                results = self.sp.next(results)
            else:
                break
        return tracks

    def analyze_albums_for_vinyl(self, playlist_id, threshold=0.5, minimum_album_size=4):
        """
        Analyze playlist to find albums that would be worth buying on vinyl.
        threshold: minimum percentage of album tracks that appear in playlist
        minimum_album_size: minimum number of songs the album must have to be considered
        """
        playlist_tracks = self.get_playlist_tracks(playlist_id)
        album_track_counts = {}  # {album_id: {'total': 0, 'listened': 0, 'info': {}}}

        # Count tracks from playlist
        for track in playlist_tracks:
            if not track['track']:
                continue

            # Skip singles and EPs (albums with less than minimum_album_size tracks)
            if track['track']['album']['total_tracks'] < minimum_album_size:
                continue

            album_id = track['track']['album']['id']
            if album_id not in album_track_counts:
                album_track_counts[album_id] = {
                    'total': track['track']['album']['total_tracks'],  # Use the total tracks info from the API
                    'listened': 0,
                    'info': {
                        'name': track['track']['album']['name'],
                        'artist': track['track']['artists'][0]['name'],
                        'image_url': track['track']['album']['images'][0]['url'] if track['track']['album']['images'] else None,
                        'release_date': track['track']['album']['release_date'],
                        'spotify_url': track['track']['album']['external_urls']['spotify'],
                        'tracks_listened': set()  # Track names you listen to
                    }
                }

            album_track_counts[album_id]['listened'] += 1
            album_track_counts[album_id]['info']['tracks_listened'].add(track['track']['name'])

        # Process albums and calculate percentages
        vinyl_recommendations = []
        for album_id, data in album_track_counts.items():
            try:
                total_tracks = data['total']
                
                # Calculate percentage of album listened to
                listen_percentage = data['listened'] / total_tracks
                
                if listen_percentage >= threshold:
                    vinyl_recommendations.append({
                        'id': album_id,
                        'name': data['info']['name'],
                        'artist': data['info']['artist'],
                        'image_url': data['info']['image_url'],
                        'release_date': data['info']['release_date'],
                        'spotify_url': data['info']['spotify_url'],
                        'total_tracks': total_tracks,
                        'listened_tracks': data['listened'],
                        'percentage': listen_percentage * 100,
                        'tracks_listened': list(data['info']['tracks_listened'])
                    })
            except Exception as e:
                print(f"Error processing album {album_id}: {str(e)}")
                continue

        # Sort by percentage (highest first) and then by number of tracks listened
        vinyl_recommendations.sort(key=lambda x: (x['percentage'], x['listened_tracks']), reverse=True)
        return vinyl_recommendations