"""Simplified storage management without per-user quotas"""
import logging
from sqlalchemy.orm import Session
from typing import Dict, List
from pathlib import Path
import os

from ..database import SessionLocal
from ..models.song import UserLibrary
from ..services.elasticsearch_service import ElasticsearchService
from ..config import settings

logger = logging.getLogger(__name__)

class SimpleStorageService:
    """Simplified storage management - no quotas, just cleanup"""
    
    def __init__(self):
        self.es_service = ElasticsearchService()
    
    async def get_storage_stats(self) -> Dict[str, any]:
        """Get overall storage statistics"""
        try:
            # Get total songs and size from Elasticsearch
            all_songs = await self.es_service.get_all_songs()
            
            total_songs = len(all_songs)
            total_size_bytes = sum(song.get('file_size', 0) for song in all_songs)
            total_size_mb = total_size_bytes // (1024 * 1024)
            
            # Get total users with songs
            db = SessionLocal()
            try:
                active_users = db.query(UserLibrary.user_id).distinct().count()
            finally:
                db.close()
            
            return {
                "total_songs": total_songs,
                "total_size_mb": total_size_mb,
                "total_size_bytes": total_size_bytes,
                "active_users": active_users,
                "avg_songs_per_user": total_songs / max(active_users, 1)
            }
            
        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {
                "total_songs": 0,
                "total_size_mb": 0,
                "total_size_bytes": 0,
                "active_users": 0,
                "avg_songs_per_user": 0
            }
    
    async def cleanup_orphaned_files(self) -> Dict[str, int]:
        """Remove files that haven't been streamed in 6 months"""
        try:
            # Get all songs from Elasticsearch
            all_songs = await self.es_service.get_all_songs()
            
            # Calculate cutoff date (6 months ago)
            from datetime import datetime, timedelta
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            
            orphaned_count = 0
            freed_bytes = 0
            
            for song_data in all_songs:
                spotify_id = song_data.get('spotify_id')
                last_streamed_str = song_data.get('last_streamed')
                
                # If song has never been streamed, check creation date
                if not last_streamed_str:
                    created_at_str = song_data.get('created_at')
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                            if created_at < six_months_ago:
                                # Song is old and never streamed
                                should_delete = True
                            else:
                                should_delete = False
                        except:
                            should_delete = False
                    else:
                        should_delete = False
                else:
                    # Check if last stream was more than 6 months ago
                    try:
                        last_streamed = datetime.fromisoformat(last_streamed_str.replace('Z', '+00:00'))
                        should_delete = last_streamed < six_months_ago
                    except:
                        should_delete = False
                
                if should_delete:
                    # This file is stale (not streamed in 6 months)
                    file_path = Path(song_data.get('file_path', ''))
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        orphaned_count += 1
                        freed_bytes += file_size
                        logger.info(f"Removed stale file (6+ months old): {file_path}")
                    
                    # Remove from Elasticsearch
                    await self.es_service.delete_song(spotify_id)
            
            freed_mb = freed_bytes // (1024 * 1024)
            logger.info(f"Cleanup complete: {orphaned_count} stale files, {freed_mb}MB freed")
            
            return {
                "files_removed": orphaned_count,
                "bytes_freed": freed_bytes,
                "mb_freed": freed_mb
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"files_removed": 0, "bytes_freed": 0, "mb_freed": 0}
    
    async def get_user_library_stats(self, user_id: int) -> Dict[str, int]:
        """Get stats for a specific user's library"""
        db = SessionLocal()
        try:
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
            
            return {
                "song_count": song_count,
                "total_size_mb": total_size_bytes // (1024 * 1024),
                "total_size_bytes": total_size_bytes
            }
            
        except Exception as e:
            logger.error(f"Error getting user library stats: {e}")
            return {"song_count": 0, "total_size_mb": 0, "total_size_bytes": 0}
        finally:
            db.close()
