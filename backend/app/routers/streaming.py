"""Music streaming endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import logging

from ..database import get_db
from ..models.user import User
from ..models.song import UserLibrary
from ..routers.auth import get_current_user
from ..services.elasticsearch_service import ElasticsearchService
from ..utils.validation import validate_spotify_id

router = APIRouter(prefix="/stream", tags=["streaming"])
logger = logging.getLogger(__name__)

@router.get("/play/{spotify_id}")
async def stream_song(
    spotify_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream a song and update last_played timestamp (Elasticsearch-centric approach)"""
    try:
        # Validate Spotify ID
        spotify_id = validate_spotify_id(spotify_id)
        
        # Get song from Elasticsearch
        es_service = ElasticsearchService()
        song_doc = await es_service.get_song(spotify_id)
        
        if not song_doc or song_doc.get("download_status") != "completed":
            raise HTTPException(status_code=404, detail="Song not found or not downloaded")
        
        # Check if file exists
        file_path_str = song_doc.get("file_path")
        if not file_path_str:
            raise HTTPException(status_code=404, detail="Audio file path not set")
            
        file_path = Path(file_path_str)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found on disk")
        
        # Update user's play count if they have it in their library
        user_library_entry = db.query(UserLibrary).filter(
            UserLibrary.user_id == current_user.id,
            UserLibrary.spotify_id == spotify_id
        ).first()
        
        if user_library_entry:
            user_library_entry.play_count += 1
            from datetime import datetime
            user_library_entry.last_played = datetime.utcnow()
            db.commit()
        
        # Update last_streamed timestamp in Elasticsearch
        await es_service.update_last_streamed(spotify_id)
        
        # Return the audio file
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=f"{song_doc.get('title', 'Unknown')} - {song_doc.get('artist', 'Unknown')}.mp3"
        )
        
    except Exception as e:
        logger.error(f"Error streaming song {spotify_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream song")

@router.post("/mark-played/{spotify_id}")
async def mark_song_played(
    spotify_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a song as played (for web players that handle streaming differently)"""
    try:
        # Validate Spotify ID
        spotify_id = validate_spotify_id(spotify_id)
        
        # Get song from Elasticsearch to verify it exists and is completed
        es_service = ElasticsearchService()
        song_doc = await es_service.get_song(spotify_id)
        
        if not song_doc or song_doc.get("download_status") != "completed":
            raise HTTPException(status_code=404, detail="Song not found or not downloaded")
        
        # Update user's play count if they have it in their library
        user_library_entry = db.query(UserLibrary).filter(
            UserLibrary.user_id == current_user.id,
            UserLibrary.spotify_id == spotify_id
        ).first()
        
        if user_library_entry:
            user_library_entry.play_count += 1
            from datetime import datetime
            user_library_entry.last_played = datetime.utcnow()
            db.commit()
        
        # Update last_streamed timestamp in Elasticsearch
        await es_service.update_last_streamed(spotify_id)
        
        return {"message": "Song marked as played", "spotify_id": spotify_id}
        
    except Exception as e:
        logger.error(f"Error marking song as played {spotify_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark song as played")
