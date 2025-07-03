import yt_dlp
import os
import logging
import asyncio
from pathlib import Path
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import tempfile
import shutil
import time

from ..database import SessionLocal
from ..models.song import DownloadStatus
from ..services.elasticsearch_service import ElasticsearchService
from ..services.spotify_service import SpotifyService
from ..services.image_service import ImageService
from ..config import settings
from ..constants import AudioConfig

logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self):
        """Initialize download service"""
        self.download_path = Path(settings.MUSIC_DOWNLOAD_PATH)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.storage_path = Path(settings.MUSIC_STORAGE_PATH)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.es_service = ElasticsearchService()
        self.spotify_service = SpotifyService()
        self.image_service = ImageService()
    
    def _get_temp_download_path(self, spotify_id: str) -> Path:
        """Generate temporary download path for a song"""
        prefix = spotify_id[:2]
        temp_path = self.download_path / prefix
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path / f"{spotify_id}.mp3"
    
    def _get_final_storage_path(self, spotify_id: str) -> Path:
        """Generate final storage path for a song"""
        prefix = spotify_id[:2]
        final_path = self.storage_path / prefix
        final_path.mkdir(parents=True, exist_ok=True)
        return final_path / f"{spotify_id}.mp3"
    
    async def download_song(self, spotify_id: str) -> bool:
        """Download a song by Spotify ID to central storage with race condition protection"""
        db = SessionLocal()
        
        try:
            # CRITICAL FIX: Simple file-based locking (Windows compatible)
            lock_path = self.download_path / f"{spotify_id}.downloading"
            
            # Check if another process is downloading (atomic operation)
            try:
                lock_path.touch(exist_ok=False)  # Fails if file exists
            except FileExistsError:
                logger.info(f"Song {spotify_id} is already being downloaded")
                # Wait a bit and check if download completed
                for _ in range(30):  # Wait up to 30 seconds
                    await asyncio.sleep(1)
                    if await self.es_service.song_exists(spotify_id):
                        return True
                return False
            
            # Double-check if already downloaded (race condition protection)
            if await self.es_service.song_exists(spotify_id):
                lock_path.unlink(missing_ok=True)  # Cleanup lock
                logger.info(f"Song {spotify_id} already exists, skipping download")
                return True
            
            # Update Elasticsearch with downloading status
            await self.es_service.update_song_status(spotify_id, "downloading")
            
            # Get song metadata from Spotify
            track_details = await self.spotify_service.get_track(spotify_id)
            if not track_details:
                await self.es_service.update_song_status(spotify_id, "failed")
                return False
            
            # Search YouTube for the song
            search_query = f"{track_details['artists'][0]['name']} - {track_details['name']}"
            youtube_url = self._search_youtube(search_query)
            if not youtube_url:
                await self.es_service.update_song_status(spotify_id, "failed")
                return False
            
            # Generate temporary download path and final storage path
            temp_file_path = self._get_temp_download_path(spotify_id)
            final_file_path = self._get_final_storage_path(spotify_id)
            
            # Download the audio to temporary location
            if self._download_audio(youtube_url, temp_file_path):
                # Move file from temp to final storage location
                try:
                    shutil.move(str(temp_file_path), str(final_file_path))
                    logger.info(f"Moved downloaded file from {temp_file_path} to {final_file_path}")
                except Exception as e:
                    logger.error(f"Failed to move file from temp to storage: {e}")
                    await self.es_service.update_song_status(spotify_id, "failed")
                    return False
                # Download album artwork
                original_image_url = track_details["album"]["images"][0]["url"] if track_details["album"]["images"] else None
                local_image_path = None
                
                if original_image_url:
                    local_image_path = self.image_service.download_album_art(spotify_id, original_image_url)
                
                # Update Elasticsearch with completed download info
                update_data = {
                    "file_path": str(final_file_path),
                    "file_size": final_file_path.stat().st_size if final_file_path.exists() else 0,
                    "youtube_url": youtube_url,
                    "download_status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Update thumbnail if we have it
                if local_image_path:
                    update_data["thumbnail_path"] = local_image_path
                
                success = await self.es_service.update_song(spotify_id, update_data)
                
                if success:
                    logger.info(f"Successfully downloaded and indexed: {track_details['name']}")
                    return True
                else:
                    await self.es_service.update_song_status(spotify_id, "failed")
                    return False
            else:
                await self.es_service.update_song_status(spotify_id, "failed")
                return False
            
        except Exception as e:
            logger.error(f"Download error for song {spotify_id}: {e}")
            await self.es_service.update_song_status(spotify_id, "failed")
            return False
        finally:
            db.close()
            # Clean up lock file
            lock_path.unlink(missing_ok=True)
    
    def _search_youtube(self, query: str) -> Optional[str]:
        """Search YouTube for a song and return the best match URL"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch1:',  # Search and get first result
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                
                if info and 'entries' in info and info['entries']:
                    video_url = info['entries'][0]['webpage_url']
                    logger.info(f"Found YouTube URL: {video_url}")
                    return video_url
                
        except Exception as e:
            logger.error(f"YouTube search error: {e}")
        
        return None
    
    def _download_audio(self, youtube_url: str, file_path: Path) -> bool:
        """Download audio from YouTube URL to specified path"""
        try:
            # Remove .mp3 extension from file_path for the template
            base_path = file_path.with_suffix('')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': AudioConfig.DEFAULT_FORMAT,
                'audioquality': str(settings.DEFAULT_AUDIO_QUALITY),
                'outtmpl': str(base_path) + '.%(ext)s',
                'quiet': False,  # Enable logging to see what's happening
                'no_warnings': False,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': AudioConfig.DEFAULT_FORMAT,
                    'preferredquality': str(settings.DEFAULT_AUDIO_QUALITY),
                    'nopostoverwrites': False,
                }],
                'prefer_ffmpeg': True,
                'keepvideo': False,
            }
            
            logger.info(f"Starting download from {youtube_url} to {base_path}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
                
                # Check if the target MP3 file was created
                if file_path.exists() and file_path.stat().st_size > 0:
                    logger.info(f"Download successful: {file_path} ({file_path.stat().st_size} bytes)")
                    return True
                
                # Check for MP3 file with base name
                mp3_file = base_path.with_suffix('.mp3')
                if mp3_file.exists() and mp3_file.stat().st_size > 0:
                    if mp3_file != file_path:
                        logger.info(f"Moving {mp3_file} to {file_path}")
                        shutil.move(str(mp3_file), str(file_path))
                    logger.info(f"Download successful: {file_path} ({file_path.stat().st_size} bytes)")
                    return True
                
                # Check for other formats that might need conversion
                for ext in ['.m4a', '.webm', '.opus', '.wav', '.mhtml']:
                    potential_file = base_path.with_suffix(ext)
                    if potential_file.exists() and potential_file.stat().st_size > 0:
                        logger.info(f"Found {ext} file, moving to {file_path}")
                        shutil.move(str(potential_file), str(file_path))
                        logger.info(f"Download successful: {file_path} ({file_path.stat().st_size} bytes)")
                        return True
            
            logger.error(f"No output file found after download. Expected: {file_path}")
            # List files in the directory to see what was created
            parent_dir = file_path.parent
            if parent_dir.exists():
                files = list(parent_dir.glob('*'))
                logger.error(f"Files in {parent_dir}: {files}")
            
            return False
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return False
    
    def _make_safe_filename(self, filename: str) -> str:
        """Create a safe filename by removing/replacing invalid characters"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove multiple spaces and trim
        filename = ' '.join(filename.split())
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    async def get_download_progress(self, spotify_id: str) -> dict:
        """Get download progress for a song by Spotify ID"""
        try:
            song = await self.es_service.get_song(spotify_id)
            if not song:
                return {"error": "Song not found"}
            
            return {
                "spotify_id": spotify_id,
                "title": song.get("title", "Unknown"),
                "artist": song.get("artist", "Unknown"),
                "status": song.get("download_status", "unknown"),
                "file_path": song.get("file_path"),
                "youtube_url": song.get("youtube_url")
            }
        except Exception as e:
            logger.error(f"Error getting download progress: {e}")
            return {"error": str(e)}
    
    def download_song_sync(self, spotify_id: str) -> dict:
        """Synchronous version of download_song for use in Celery tasks"""
        try:
            # Use an event loop to run the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.download_song(spotify_id))
                if result:
                    return {
                        "success": True,
                        "file_path": self.es_service.get_file_path(spotify_id),
                        "spotify_id": spotify_id
                    }
                else:
                    return {
                        "success": False,
                        "error": "Download failed"
                    }
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Sync download error for {spotify_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
