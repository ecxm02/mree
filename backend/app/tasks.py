from sqlalchemy.orm import Session
from .database import SessionLocal
from .models.song import UserLibrary
from .services.download_service import DownloadService
from .services.elasticsearch_service import ElasticsearchService
from .services.backup_service import backup_service
from .services.image_service import ImageService
from .constants import SearchConfig
from .worker import celery_app
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, max_retries=3)
def download_song(self, spotify_id: str, user_id: int):
    """
    Background task to download a song from YouTube and index in Elasticsearch.
    
    Architecture:
    - Elasticsearch: Primary music catalog (metadata, file paths, download status)
    - PostgreSQL: User-specific data only (libraries, playlists, user stats)
    """
    logger.info(f"DOWNLOAD TASK STARTED: Processing download for Spotify ID {spotify_id}, User ID {user_id}")
    es_service = ElasticsearchService()
    
    try:
        # Step 1: Check if song already exists in Elasticsearch with completed download
        existing_song = es_service.get_song_sync(spotify_id)
        if existing_song and existing_song.get("download_status") == "completed":
            logger.info(f"Song {spotify_id} already downloaded, adding to user library")
            
            # Add to user's library if not already there
            db: Session = SessionLocal()
            try:
                existing_library = db.query(UserLibrary).filter(
                    UserLibrary.user_id == user_id,
                    UserLibrary.spotify_id == spotify_id
                ).first()
                
                if not existing_library:
                    new_library_entry = UserLibrary(
                        user_id=user_id,
                        spotify_id=spotify_id
                    )
                    db.add(new_library_entry)
                    db.commit()
                    
                    # Increment download count in Elasticsearch
                    es_service.increment_download_count_sync(spotify_id)
                    
            finally:
                db.close()
                
            return {
                "status": "completed",
                "spotify_id": spotify_id,
                "message": "Song already downloaded, added to library"
            }
        
        # Step 2: Create/update song entry in Elasticsearch with downloading status
        if not existing_song:
            # Get song metadata from Spotify first
            from .services.spotify_service import SpotifyService
            spotify_service = SpotifyService()
            track_info = spotify_service.get_track_sync(spotify_id)
            
            # Download album artwork
            image_service = ImageService()
            original_image_url = track_info["album"]["images"][0]["url"] if track_info["album"]["images"] else None
            local_image_path = None
            
            if original_image_url:
                local_image_path = image_service.download_album_art(spotify_id, original_image_url)
            
            song_doc = {
                "spotify_id": spotify_id,
                "title": track_info["name"],
                "artist": ", ".join([artist["name"] for artist in track_info["artists"]]),
                "album": track_info["album"]["name"],
                "duration": track_info["duration_ms"] // 1000,
                "thumbnail_path": local_image_path,
                "original_thumbnail_url": original_image_url,
                "download_status": "downloading",
                "download_count": 1,
                "first_requested_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            es_service.add_song_sync(song_doc)
        else:
            # Update status to downloading
            es_service.update_song_status_sync(spotify_id, "downloading")
        
        # Step 3: Download the song using synchronous download service
        logger.info(f"Starting actual download for {spotify_id}")
        download_service = DownloadService()
        result = download_service.download_song_sync(spotify_id)
        
        logger.info(f"Download service returned: {result}")
        
        if result["success"]:
            # Step 4: Update Elasticsearch with completed download info
            update_doc = {
                "spotify_id": spotify_id,
                "file_path": result["file_path"],
                "file_size": result.get("file_size"),
                "youtube_url": result.get("youtube_url"),
                "download_status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            es_service.update_song_sync(spotify_id, update_doc)
            
            # Step 5: Add to user's library (PostgreSQL)
            db: Session = SessionLocal()
            try:
                existing_library = db.query(UserLibrary).filter(
                    UserLibrary.user_id == user_id,
                    UserLibrary.spotify_id == spotify_id
                ).first()
                
                if not existing_library:
                    new_library_entry = UserLibrary(
                        user_id=user_id,
                        spotify_id=spotify_id
                    )
                    db.add(new_library_entry)
                    db.commit()
            finally:
                db.close()
            
            logger.info(f"Successfully downloaded and indexed song: {spotify_id}")
            
            return {
                "status": "completed",
                "spotify_id": spotify_id,
                "file_path": result["file_path"],
                "message": "Song downloaded and added to library"
            }
        else:
            # Update Elasticsearch with failed status
            es_service.update_song_status_sync(spotify_id, "failed")
            logger.error(f"Failed to download song: {spotify_id} - {result.get('error')}")
            
            return {
                "status": "failed",
                "spotify_id": spotify_id,
                "error": result.get("error")
            }
        
    except Exception as exc:
        logger.error(f"Download task failed for {spotify_id}: {str(exc)}")
        
        # Update Elasticsearch status to failed
        try:
            es_service.update_song_status_sync(spotify_id, "failed")
        except:
            pass
        
        # Retry the task with exponential backoff
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying download task for song {spotify_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {"status": "error", "message": str(exc)}

@celery_app.task
def process_audio(file_path: str, song_id: int):
    """
    Background task to process audio files (normalize volume, extract metadata, etc.)
    """
    try:
        logger.info(f"Processing audio for song {song_id}: {file_path}")
        
        # TODO: Implement audio processing
        # - Normalize audio levels
        # - Extract duration, bitrate, etc.
        # - Generate thumbnails if needed
        # - Validate audio quality
        
        return {"status": "completed", "song_id": song_id}
        
    except Exception as exc:
        logger.error(f"Audio processing failed for song {song_id}: {str(exc)}")
        return {"status": "error", "message": str(exc)}

@celery_app.task
def cleanup_failed_downloads():
    """
    Periodic task to clean up failed downloads and retry them.
    Now uses Elasticsearch to find and reset stuck downloads.
    """
    es_service = ElasticsearchService()
    
    try:
        # Find songs stuck in downloading status for more than 1 hour
        from datetime import datetime, timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=1)
        
        # Search for songs with downloading status that are old
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"download_status": "downloading"}},
                        {"range": {"updated_at": {"lt": cutoff_time.isoformat()}}}
                    ]
                }
            }
        }
        
        stuck_songs = es_service.search_raw_sync(query)
        reset_count = 0
        
        for hit in stuck_songs.get('hits', {}).get('hits', []):
            song_data = hit['_source']
            spotify_id = song_data['spotify_id']
            
            logger.warning(f"Resetting stuck download: {song_data.get('title', spotify_id)}")
            
            # Reset status to pending for retry
            es_service.update_song_status_sync(spotify_id, "pending")
            reset_count += 1
        
        return {"status": "completed", "reset_count": reset_count}
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        return {"status": "error", "message": str(exc)}

@celery_app.task
def daily_backup():
    """
    Daily backup task for all databases.
    Scheduled to run at the configured hour (default 3 AM).
    """
    try:
        logger.info("Starting daily backup task...")
        
        # Create backup
        backup_result = backup_service.create_backup()
        
        if backup_result["status"] == "success":
            logger.info(f"Daily backup completed successfully: {backup_result.get('backup_path')}")
            
            # Clean up old backups
            cleanup_result = backup_service.cleanup_old_backups()
            
            if cleanup_result["status"] == "success":
                logger.info(f"Cleaned up {cleanup_result['deleted_count']} old backups, freed {cleanup_result['freed_space_mb']} MB")
            
            return {
                "status": "success",
                "backup": backup_result,
                "cleanup": cleanup_result
            }
        else:
            logger.error(f"Daily backup failed: {backup_result.get('error')}")
            return backup_result
            
    except Exception as exc:
        logger.error(f"Daily backup task failed: {str(exc)}")
        return {"status": "error", "message": str(exc)}

@celery_app.task
def manual_backup():
    """
    Manual backup task that can be triggered on demand.
    """
    try:
        logger.info("Starting manual backup task...")
        
        backup_result = backup_service.create_backup()
        
        if backup_result["status"] == "success":
            logger.info(f"Manual backup completed successfully: {backup_result.get('backup_path')}")
        else:
            logger.error(f"Manual backup failed: {backup_result.get('error')}")
        
        return backup_result
        
    except Exception as exc:
        logger.error(f"Manual backup task failed: {str(exc)}")
        return {"status": "error", "message": str(exc)}

@celery_app.task
def cleanup_unused_images():
    """
    Periodic task to clean up unused album artwork files.
    """
    from .config import settings
    
    if not settings.IMAGE_CLEANUP_ENABLED:
        logger.info("Image cleanup is disabled in configuration")
        return {"status": "disabled", "message": "Image cleanup is disabled"}
    
    try:
        logger.info("Starting image cleanup task...")
        
        # Get all active spotify IDs from Elasticsearch
        es_service = ElasticsearchService()
        query = {
            "query": {"match_all": {}},
            "_source": ["spotify_id"],
            "size": SearchConfig.DEFAULT_ELASTICSEARCH_SIZE
        }
        
        result = es_service.search_raw_sync(query)
        active_spotify_ids = [hit["_source"]["spotify_id"] for hit in result.get("hits", {}).get("hits", [])]
        
        # Clean up unused images
        image_service = ImageService()
        cleanup_result = image_service.cleanup_unused_images(active_spotify_ids)
        
        if cleanup_result["status"] == "success":
            logger.info(f"Image cleanup completed: deleted {cleanup_result['deleted_count']} files, freed {cleanup_result['freed_space_mb']} MB")
        
        return cleanup_result
        
    except Exception as exc:
        logger.error(f"Image cleanup task failed: {str(exc)}")
        return {"status": "error", "message": str(exc)}


@celery_app.task
def update_metrics():
    """Update Prometheus metrics periodically"""
    try:
        from .middleware.metrics import update_background_metrics
        update_background_metrics()
        logger.info("Metrics updated successfully")
        return {"status": "success", "timestamp": datetime.utcnow().isoformat()}
    except Exception as exc:
        logger.error(f"Metrics update task failed: {str(exc)}")
        return {"status": "error", "message": str(exc)}
