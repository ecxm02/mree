from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..models.song_improved import Song, UserLibrary, DownloadStatus
from ..schemas.songs import SongSearch, SearchResponse, SpotifySearchResult, SongResponse
from ..routers.auth import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.download_service import DownloadService

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/download/{spotify_id}", response_model=SongResponse)
async def request_download(
    spotify_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request download of a song by Spotify ID - IMPROVED VERSION"""
    
    # Step 1: Check if song already exists GLOBALLY
    existing_song = db.query(Song).filter(Song.spotify_id == spotify_id).first()
    
    if existing_song:
        # Song exists! Check if user already has it in their library
        user_library_entry = db.query(UserLibrary).filter(
            UserLibrary.user_id == current_user.id,
            UserLibrary.song_id == existing_song.id
        ).first()
        
        if user_library_entry:
            # User already has this song
            return create_song_response(existing_song, user_library_entry)
        else:
            # Song exists but user doesn't have it - add to their library
            new_library_entry = UserLibrary(
                user_id=current_user.id,
                song_id=existing_song.id
            )
            db.add(new_library_entry)
            
            # Increment download count
            existing_song.download_count += 1
            db.commit()
            db.refresh(new_library_entry)
            
            return create_song_response(existing_song, new_library_entry)
    
    # Step 2: Song doesn't exist - create it and download
    spotify_service = SpotifyService()
    try:
        track_details = await spotify_service.get_track(spotify_id)
        
        # Create new song record (global)
        new_song = Song(
            title=track_details["name"],
            artist=", ".join([artist["name"] for artist in track_details["artists"]]),
            album=track_details["album"]["name"],
            duration=track_details["duration_ms"] // 1000,
            spotify_id=spotify_id,
            thumbnail_url=track_details["album"]["images"][0]["url"] if track_details["album"]["images"] else None,
            download_status=DownloadStatus.PENDING,
            first_requested_by=current_user.id,
            download_count=1
        )
        
        db.add(new_song)
        db.commit()
        db.refresh(new_song)
        
        # Add to user's library
        new_library_entry = UserLibrary(
            user_id=current_user.id,
            song_id=new_song.id
        )
        db.add(new_library_entry)
        db.commit()
        db.refresh(new_library_entry)
        
        # Start background download task (only downloads once!)
        download_service = DownloadService()
        background_tasks.add_task(download_service.download_song, new_song.id)
        
        return create_song_response(new_song, new_library_entry)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download request failed: {str(e)}")

def create_song_response(song: Song, library_entry: UserLibrary) -> SongResponse:
    """Helper function to create consistent song responses"""
    return SongResponse(
        id=song.id,
        title=song.title,
        artist=song.artist,
        album=song.album,
        duration=song.duration,
        spotify_id=song.spotify_id,
        youtube_url=song.youtube_url,
        file_path=song.file_path,
        thumbnail_url=song.thumbnail_url,
        download_status=song.download_status.value,
        created_at=library_entry.added_at,  # User's add date, not song creation
        is_favorite=library_entry.is_favorite,
        play_count=library_entry.play_count
    )

@router.get("/library", response_model=List[SongResponse])
async def get_user_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's personal music library"""
    
    # Join user library with songs
    library_with_songs = db.query(UserLibrary, Song).join(
        Song, UserLibrary.song_id == Song.id
    ).filter(
        UserLibrary.user_id == current_user.id,
        Song.download_status == DownloadStatus.COMPLETED
    ).order_by(UserLibrary.added_at.desc()).all()
    
    return [
        create_song_response(song, library_entry)
        for library_entry, song in library_with_songs
    ]
