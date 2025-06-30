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
    
    def get_track_sync(self, track_id: str) -> Dict[str, Any]:
        """Synchronous version of get_track for Celery tasks"""
        try:
            logger.info(f"Getting Spotify track (sync): {track_id}")
            track = self.sp.track(track_id)
            return track
        except Exception as e:
            logger.error(f"Spotify track fetch error (sync): {e}")
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
    
    async def get_track_with_images(self, track_id: str) -> Dict[str, Any]:
        """Get detailed track information with all image sizes"""
        try:
            logger.info(f"Getting Spotify track with images: {track_id}")
            track = self.sp.track(track_id)
            
            # Extract all image sizes
            images = track["album"]["images"]
            image_data = {
                "large": images[0]["url"] if len(images) > 0 else None,      # 640x640
                "medium": images[1]["url"] if len(images) > 1 else None,     # 300x300  
                "small": images[2]["url"] if len(images) > 2 else None       # 64x64
            } if images else {}
            
            # Add image data to track info
            track["image_urls"] = image_data
            
            return track
        except Exception as e:
            logger.error(f"Spotify track with images fetch error: {e}")
            raise
