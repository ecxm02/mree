from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models.user import User
from ..models.song import UserLibrary, DownloadQueue, DownloadStatus
from ..schemas.songs import SongSearch, SearchResponse, SpotifySearchResult, SongResponse
from ..routers.auth import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.download_service import DownloadService
from ..services.elasticsearch_service import ElasticsearchService

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/spotify", response_model=SearchResponse)
async def search_spotify(
    search: SongSearch,
    current_user: User = Depends(get_current_user)
):
    """Search for songs on Spotify"""
    spotify_service = SpotifyService()
    
    try:
        results = await spotify_service.search_tracks(search.query, limit=search.limit)
        
        spotify_results = [
            SpotifySearchResult(
                spotify_id=track["id"],
                title=track["name"],
                artist=", ".join([artist["name"] for artist in track["artists"]]),
                album=track["album"]["name"],
                duration=track["duration_ms"] // 1000,  # Convert to seconds
                preview_url=track.get("preview_url"),
                thumbnail_url=track["album"]["images"][0]["url"] if track["album"]["images"] else None
            )
            for track in results["tracks"]["items"]
        ]
        
        return SearchResponse(
            results=spotify_results,
            total=results["tracks"]["total"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spotify search failed: {str(e)}")

@router.post("/download/{spotify_id}", response_model=dict)
async def request_download(
    spotify_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request download of a song by Spotify ID"""
    
    es_service = ElasticsearchService()
    
    # Step 1: Check if user already has this song
    user_library_entry = db.query(UserLibrary).filter(
        UserLibrary.user_id == current_user.id,
        UserLibrary.spotify_id == spotify_id
    ).first()
    
    if user_library_entry:
        return {
            "message": "Song already in your library",
            "spotify_id": spotify_id,
            "added_at": user_library_entry.added_at
        }
    
    # Step 2: Check if song exists in Elasticsearch (already downloaded)
    if await es_service.song_exists(spotify_id):
        # Song exists, just add to user's library
        new_library_entry = UserLibrary(
            user_id=current_user.id,
            spotify_id=spotify_id
        )
        db.add(new_library_entry)
        
        # Increment download count in Elasticsearch
        await es_service.update_download_count(spotify_id)
        
        db.commit()
        return {
            "message": "Song added to your library (already downloaded)",
            "spotify_id": spotify_id,
            "status": "instant"
        }
    
    # Step 3: Song doesn't exist, need to download
    # Check if already in download queue
    existing_queue = db.query(DownloadQueue).filter(
        DownloadQueue.spotify_id == spotify_id
    ).first()
    
    if not existing_queue:
        # Add to download queue
        queue_item = DownloadQueue(
            spotify_id=spotify_id,
            requested_by=current_user.id,
            status=DownloadStatus.PENDING
        )
        db.add(queue_item)
        db.commit()
        
        # Start background download
        download_service = DownloadService()
        background_tasks.add_task(download_service.download_song, spotify_id)
    
    # Add to user's library (even if download is pending)
    new_library_entry = UserLibrary(
        user_id=current_user.id,
        spotify_id=spotify_id
    )
    db.add(new_library_entry)
    db.commit()
    
    return {
        "message": "Download requested, song added to your library",
        "spotify_id": spotify_id,
        "status": "downloading"
    }

@router.get("/library", response_model=List[SongResponse])
async def get_user_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's personal music library"""
    
    # Get user's library entries
    library_entries = db.query(UserLibrary).filter(
        UserLibrary.user_id == current_user.id
    ).order_by(UserLibrary.added_at.desc()).all()
    
    if not library_entries:
        return []
    
    # Get song details from Elasticsearch
    es_service = ElasticsearchService()
    songs_data = []
    
    for entry in library_entries:
        song_data = await es_service.get_song(entry.spotify_id)
        if song_data:  # Only include songs that are actually downloaded
            songs_data.append(SongResponse(
                id=0,  # Not using DB IDs anymore
                title=song_data["title"],
                artist=song_data["artist"],
                album=song_data["album"],
                duration=song_data["duration"],
                spotify_id=song_data["spotify_id"],
                youtube_url=song_data.get("youtube_url"),
                file_path=song_data["file_path"],
                thumbnail_url=song_data.get("thumbnail_url"),
                download_status="completed",
                created_at=entry.added_at
            ))
    
    return songs_data

@router.get("/popular", response_model=List[SongResponse])
async def get_popular_songs(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get most popular songs from Elasticsearch"""
    
    es_service = ElasticsearchService()
    popular_songs = await es_service.get_popular_songs(limit=limit)
    
    return [
        SongResponse(
            id=0,
            title=song["title"],
            artist=song["artist"],
            album=song["album"],
            duration=song["duration"],
            spotify_id=song["spotify_id"],
            youtube_url=song.get("youtube_url"),
            file_path=song["file_path"],
            thumbnail_url=song.get("thumbnail_url"),
            download_status="completed",
            created_at=song["created_at"]
        )
        for song in popular_songs
    ]

@router.post("/local", response_model=List[SongResponse])
async def search_local_songs(
    search: SongSearch,
    current_user: User = Depends(get_current_user)
):
    """Search downloaded songs by title, artist, or album"""
    
    es_service = ElasticsearchService()
    
    try:
        # Search in Elasticsearch using title, artist, album
        results = await es_service.search_songs(search.query, limit=search.limit)
        
        return [
            SongResponse(
                id=0,  # Not using database ID since this is Elasticsearch
                title=song["title"],
                artist=song["artist"],
                album=song["album"],
                duration=song["duration"],
                spotify_id=song["spotify_id"],
                youtube_url=song.get("youtube_url"),
                file_path=song["file_path"],
                thumbnail_url=song.get("thumbnail_url"),
                download_status="completed",  # Only completed songs are in Elasticsearch
                created_at=song.get("created_at")
            )
            for song in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local search failed: {str(e)}")

@router.get("/local/by-artist/{artist_name}", response_model=List[SongResponse])
async def search_by_artist(
    artist_name: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search downloaded songs by artist name"""
    
    es_service = ElasticsearchService()
    
    try:
        results = await es_service.search_songs(f"artist:{artist_name}", limit=limit)
        
        return [
            SongResponse(
                id=0,
                title=song["title"],
                artist=song["artist"],
                album=song["album"],
                duration=song["duration"],
                spotify_id=song["spotify_id"],
                youtube_url=song.get("youtube_url"),
                file_path=song["file_path"],
                thumbnail_url=song.get("thumbnail_url"),
                download_status="completed",
                created_at=song.get("created_at")
            )
            for song in results
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Artist search failed: {str(e)}")
