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
from ..models.song import DownloadQueue, DownloadStatus
from ..services.elasticsearch_service import ElasticsearchService
from ..services.spotify_service import SpotifyService
from ..config import settings

logger = logging.getLogger(__name__)

class DownloadService:
    def __init__(self):
        """Initialize download service"""
        self.download_path = Path(settings.MUSIC_DOWNLOAD_PATH)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.es_service = ElasticsearchService()
        self.spotify_service = SpotifyService()
    
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
            
            # Update download queue status
            queue_item = db.query(DownloadQueue).filter(
                DownloadQueue.spotify_id == spotify_id
            ).first()
            
            if queue_item:
                queue_item.status = DownloadStatus.DOWNLOADING
                db.commit()
            
            # Get song metadata from Spotify
            track_details = await self.spotify_service.get_track(spotify_id)
            if not track_details:
                if queue_item:
                    queue_item.status = DownloadStatus.FAILED
                    queue_item.error_message = "Failed to get Spotify metadata"
                    db.commit()
                return False
            
            # Search YouTube for the song
            search_query = f"{track_details['artists'][0]['name']} - {track_details['name']}"
            youtube_url = self._search_youtube(search_query)
            if not youtube_url:
                if queue_item:
                    queue_item.status = DownloadStatus.FAILED
                    queue_item.error_message = "YouTube video not found"
                    db.commit()
                return False
            
            # Generate file path (organized by spotify_id prefix)
            file_path = self.es_service.get_file_path(spotify_id)
            file_path_obj = Path(file_path)
            file_path_obj.parent.mkdir(parents=True, exist_ok=True)
            
            # Download the audio
            if self._download_audio(youtube_url, file_path_obj):
                # Add to Elasticsearch
                song_data = {
                    "spotify_id": spotify_id,
                    "title": track_details["name"],
                    "artist": ", ".join([artist["name"] for artist in track_details["artists"]]),
                    "album": track_details["album"]["name"],
                    "duration": track_details["duration_ms"] // 1000,
                    "file_path": str(file_path),
                    "file_size": file_path_obj.stat().st_size if file_path_obj.exists() else 0,
                    "thumbnail_url": track_details["album"]["images"][0]["url"] if track_details["album"]["images"] else None,
                    "youtube_url": youtube_url,
                    "download_count": 1,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                success = await self.es_service.add_song(song_data)
                
                if success:
                    # Update download queue
                    if queue_item:
                        queue_item.status = DownloadStatus.COMPLETED
                        db.commit()
                    
                    logger.info(f"Successfully downloaded and indexed: {track_details['name']}")
                    return True
                else:
                    if queue_item:
                        queue_item.status = DownloadStatus.FAILED
                        queue_item.error_message = "Failed to index in Elasticsearch"
                        db.commit()
                    return False
            else:
                if queue_item:
                    queue_item.status = DownloadStatus.FAILED
                    queue_item.error_message = "Download failed"
                    db.commit()
                return False
            
        except Exception as e:
            logger.error(f"Download error for song {spotify_id}: {e}")
            if queue_item:
                queue_item.status = DownloadStatus.FAILED
                queue_item.error_message = str(e)
                db.commit()
            return False
        finally:
            db.close()
    
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
    
    def _download_audio(self, youtube_url: str, song: Song) -> Optional[Path]:
        """Download audio from YouTube URL"""
        try:
            # Create safe filename
            safe_filename = self._make_safe_filename(f"{song.artist} - {song.title}")
            output_path = self.download_path / f"{safe_filename}.%(ext)s"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
                'outtmpl': str(output_path),
                'quiet': True,
                'no_warnings': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([youtube_url])
                
                # Find the downloaded file
                mp3_file = self.download_path / f"{safe_filename}.mp3"
                if mp3_file.exists():
                    return mp3_file
                
                # Sometimes the file extension might be different
                for ext in ['.mp3', '.m4a', '.webm', '.opus']:
                    potential_file = self.download_path / f"{safe_filename}{ext}"
                    if potential_file.exists():
                        return potential_file
            
        except Exception as e:
            logger.error(f"Download error: {e}")
        
        return None
    
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
    
    def get_download_progress(self, song_id: int) -> dict:
        """Get download progress for a song"""
        db = SessionLocal()
        try:
            song = db.query(Song).filter(Song.id == song_id).first()
            if not song:
                return {"error": "Song not found"}
            
            return {
                "song_id": song.id,
                "title": song.title,
                "artist": song.artist,
                "status": song.download_status.value,
                "file_path": song.file_path,
                "youtube_url": song.youtube_url
            }
        finally:
            db.close()
