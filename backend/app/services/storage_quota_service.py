"""User storage quota management service"""
import logging
from sqlalchemy.orm import Session
from typing import Dict, Optional
from pathlib import Path
import os

from ..database import SessionLocal
from ..models.user import User
from ..models.song import UserLibrary
from ..services.elasticsearch_service import ElasticsearchService
from ..config import settings

logger = logging.getLogger(__name__)

class StorageQuotaService:
    """Manage user storage quotas and usage tracking"""
    
    def __init__(self):
        self.es_service = ElasticsearchService()
    
    async def get_user_usage(self, user_id: int) -> Dict[str, int]:
        """Get user's current storage usage in MB"""
        db = SessionLocal()
        try:
            # Get all songs in user's library
            user_songs = db.query(UserLibrary).filter(
                UserLibrary.user_id == user_id
            ).all()
            
            total_size_bytes = 0
            song_count = len(user_songs)
            
            # Calculate total size from Elasticsearch
            for user_song in user_songs:
                song_data = await self.es_service.get_song(user_song.spotify_id)
                if song_data:
                    file_size = song_data.get('file_size', 0)
                    total_size_bytes += file_size
            
            total_size_mb = total_size_bytes // (1024 * 1024)
            
            return {
                "used_mb": total_size_mb,
                "song_count": song_count,
                "used_bytes": total_size_bytes
            }
            
        except Exception as e:
            logger.error(f"Error calculating user storage usage: {e}")
            return {"used_mb": 0, "song_count": 0, "used_bytes": 0}
        finally:
            db.close()
    
    async def get_user_quota(self, user_id: int) -> int:
        """Get user's storage quota in MB"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and hasattr(user, 'storage_quota_mb'):
                return user.storage_quota_mb
            return settings.DEFAULT_USER_QUOTA_MB
        except Exception as e:
            logger.error(f"Error getting user quota: {e}")
            return settings.DEFAULT_USER_QUOTA_MB
        finally:
            db.close()
    
    async def can_user_download(self, user_id: int, estimated_size_mb: int = 10) -> bool:
        """Check if user can download another song"""
        try:
            usage = await self.get_user_usage(user_id)
            quota = await self.get_user_quota(user_id)
            
            return (usage["used_mb"] + estimated_size_mb) <= quota
            
        except Exception as e:
            logger.error(f"Error checking download permission: {e}")
            # Be conservative - deny if we can't check
            return False
    
    async def cleanup_orphaned_files(self) -> int:
        """Remove MP3 files that are no longer referenced by any user"""
        try:
            # Get all songs from Elasticsearch
            all_songs = await self.es_service.get_all_songs()
            referenced_spotify_ids = set()
            
            # Get all songs referenced by users
            db = SessionLocal()
            try:
                user_songs = db.query(UserLibrary.spotify_id).distinct().all()
                referenced_spotify_ids = {song.spotify_id for song in user_songs}
            finally:
                db.close()
            
            # Find orphaned files
            orphaned_count = 0
            music_path = Path(settings.MUSIC_DOWNLOAD_PATH)
            
            for song_data in all_songs:
                spotify_id = song_data.get('spotify_id')
                if spotify_id not in referenced_spotify_ids:
                    # This file is orphaned
                    file_path = Path(song_data.get('file_path', ''))
                    if file_path.exists():
                        file_path.unlink()
                        orphaned_count += 1
                        logger.info(f"Removed orphaned file: {file_path}")
                    
                    # Remove from Elasticsearch
                    await self.es_service.delete_song(spotify_id)
            
            logger.info(f"Cleaned up {orphaned_count} orphaned files")
            return orphaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
