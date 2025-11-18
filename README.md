# Spotify Playlist Analyzer
## Purpose
This tool was built as a personal project that allows users to connect their Spotify account and input one of their playlists to run one of two types of analysis on it.
The analyses currently available are 'One Hit Wonders' and 'Vinyl Recommendations'
### One Hit Wonders
Once the user selects a playlist, the app looks for artists that have exactly one song on that playlist.  These songs are considered the user's 'One Hit Wonders' as they are the only song by that artist that the user listens to.  The analysis only considers the first artist listed on any given track, as it assumes that they are the primary artist.

### Vinyl Recommendations
Once the user selects a playlist, the app considers every album that has a song on that playlist.  It then looks to see how many of the total songs on that album are on the playlist.  If the proportion exceeds a threshold set by the user, then the app recommends this album for purchase (such as on vinyl) since they will enjoy at least this minimum percentage of the songs.

## How to run
To run this app, you must have a Spotify developer account to use the Spotify web API.  Once you do, fill in the relevant client_id and client_secrets in the .env file, as well as redirect_uri, which you have whitelisted on Spotify, and a secret to use for signatures.  Then, use pip or pipenv to install the dependencies listed in the pipfile, and run app.py.  Any Spotify accounts that attempt to sign in must be whitelisted on the Spotify developers dashboard.
