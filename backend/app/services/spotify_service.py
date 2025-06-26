import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import Dict, Any
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self):
        """Initialize Spotify service with credentials"""
        if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
            raise ValueError("Spotify credentials not configured")
        
        client_credentials_manager = SpotifyClientCredentials(
            client_id=settings.SPOTIFY_CLIENT_ID,
            client_secret=settings.SPOTIFY_CLIENT_SECRET
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    
    async def search_tracks(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search for tracks on Spotify"""
        try:
            logger.info(f"Searching Spotify for: {query}")
            results = self.sp.search(q=query, type="track", limit=limit)
            logger.info(f"Found {len(results['tracks']['items'])} tracks")
            return results
        except Exception as e:
            logger.error(f"Spotify search error: {e}")
            raise
    
    async def get_track(self, track_id: str) -> Dict[str, Any]:
        """Get detailed track information by Spotify ID"""
        try:
            logger.info(f"Getting Spotify track: {track_id}")
            track = self.sp.track(track_id)
            return track
        except Exception as e:
            logger.error(f"Spotify track fetch error: {e}")
            raise
    
    async def get_artist(self, artist_id: str) -> Dict[str, Any]:
        """Get artist information by Spotify ID"""
        try:
            artist = self.sp.artist(artist_id)
            return artist
        except Exception as e:
            logger.error(f"Spotify artist fetch error: {e}")
            raise
    
    async def get_album(self, album_id: str) -> Dict[str, Any]:
        """Get album information by Spotify ID"""
        try:
            album = self.sp.album(album_id)
            return album
        except Exception as e:
            logger.error(f"Spotify album fetch error: {e}")
            raise
