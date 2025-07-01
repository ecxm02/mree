from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..database import get_db
from ..models.user import User
from ..models.song import UserLibrary
from ..schemas.songs import SongSearch, SearchResponse, SpotifySearchResult, SongResponse
from ..routers.auth import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.elasticsearch_service import ElasticsearchService
from ..services.image_service import ImageService
from ..tasks import download_song

router = APIRouter(prefix="/search", tags=["search"])

def get_thumbnail_url(song_doc: dict) -> Optional[str]:
    """Get the appropriate thumbnail URL for a song with failsafe re-download"""
    spotify_id = song_doc.get("spotify_id")
    original_url = song_doc.get("original_thumbnail_url")
    if spotify_id:
        image_service = ImageService()
        return image_service.get_image_url_with_fallback(spotify_id, original_url)
    return original_url

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

@router.post("/download/{spotify_id}", response_model=Dict[str, Any])
async def request_download(
    spotify_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request download of a song by Spotify ID (Elasticsearch-centric approach)"""
    
    es_service = ElasticsearchService()
    
    # Step 1: Check if user already has this song in their library
    user_library_entry = db.query(UserLibrary).filter(
        UserLibrary.user_id == current_user.id,
        UserLibrary.spotify_id == spotify_id
    ).first()
    
    if user_library_entry:
        return {
            "message": "Song already in your library",
            "spotify_id": spotify_id,
            "status": "already_owned",
            "added_at": user_library_entry.added_at
        }
    
    # Step 2: Check if song exists in Elasticsearch (already downloaded)
    existing_song = await es_service.get_song(spotify_id)
    
    if existing_song and existing_song.get("download_status") == "completed":
        # Song exists and is complete - just add to user's library
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
            "status": "instant_add"
        }
    
    # Step 3: Song doesn't exist or isn't complete - queue download
    if existing_song and existing_song.get("download_status") in ["pending", "downloading"]:
        # Song is already being downloaded
        new_library_entry = UserLibrary(
            user_id=current_user.id,
            spotify_id=spotify_id
        )
        db.add(new_library_entry)
        db.commit()
        
        return {
            "message": "Song is being downloaded, added to your library",
            "spotify_id": spotify_id,
            "status": "downloading"
        }
    
    # Step 4: New song - add to user library and queue download
    new_library_entry = UserLibrary(
        user_id=current_user.id,
        spotify_id=spotify_id
    )
    db.add(new_library_entry)
    db.commit()
    
    # Queue background download task
    task = download_song.delay(spotify_id, current_user.id)
    
    return {
        "message": "Download started, song added to your library",
        "spotify_id": spotify_id,
        "status": "queued",
        "task_id": task.id
    }

@router.get("/library", response_model=List[SongResponse])
async def get_user_library(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's personal music library (Elasticsearch-centric approach)"""
    
    es_service = ElasticsearchService()
    
    # Get user's library entries from PostgreSQL
    library_entries = db.query(UserLibrary).filter(
        UserLibrary.user_id == current_user.id
    ).order_by(UserLibrary.added_at.desc()).all()
    
    if not library_entries:
        return []
    
    songs_data = []
    for library_entry in library_entries:
        # Get song details from Elasticsearch
        song_doc = await es_service.get_song(library_entry.spotify_id)
        
        # Only include completed downloads
        if song_doc and song_doc.get("download_status") == "completed":
            songs_data.append(SongResponse(
                id=library_entry.id,  # Use library entry ID as response ID
                title=song_doc.get("title", ""),
                artist=song_doc.get("artist", ""),
                album=song_doc.get("album", ""),
                duration=song_doc.get("duration", 0),
                spotify_id=song_doc.get("spotify_id"),
                youtube_url=song_doc.get("youtube_url"),
                file_path=song_doc.get("file_path"),
                thumbnail_url=get_thumbnail_url(song_doc),
                download_status="completed",
                created_at=library_entry.added_at
            ))
    
    return songs_data

@router.get("/popular", response_model=List[SongResponse])
async def get_popular_songs(
    limit: int = 20,
    current_user: User = Depends(get_current_user)
):
    """Get most popular songs from Elasticsearch"""
    
    es_service = ElasticsearchService()
    
    # Search for completed songs ordered by download count
    query = {
        "query": {
            "term": {"download_status": "completed"}
        },
        "sort": [
            {"download_count": {"order": "desc"}}
        ],
        "size": limit
    }
    
    results = await es_service.search_raw(query)
    
    songs_data = []
    for hit in results.get('hits', {}).get('hits', []):
        song_doc = hit['_source']
        songs_data.append(SongResponse(
            id=hit['_id'],  # Use Elasticsearch document ID
            title=song_doc.get("title", ""),
            artist=song_doc.get("artist", ""),
            album=song_doc.get("album", ""),
            duration=song_doc.get("duration", 0),
            spotify_id=song_doc.get("spotify_id"),
            youtube_url=song_doc.get("youtube_url"),
            file_path=song_doc.get("file_path"),
            thumbnail_url=get_thumbnail_url(song_doc),
            download_status="completed",
            created_at=song_doc.get("created_at")
        ))
    
    return songs_data

@router.post("/local", response_model=List[SongResponse])
async def search_local_songs(
    search: SongSearch,
    current_user: User = Depends(get_current_user)
):
    """Search downloaded songs by title, artist, or album using Elasticsearch"""
    
    es_service = ElasticsearchService()
    
    # Build Elasticsearch query for fuzzy matching across title, artist, and album
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "multi_match": {
                            "query": search.query,
                            "fields": ["title^2", "artist^1.5", "album"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "minimum_should_match": "75%"
                        }
                    }
                ]
            }
        },
        "size": search.limit
    }
    
    results = await es_service.search_raw(query)
    
    songs_data = []
    for hit in results.get('hits', {}).get('hits', []):
        song_doc = hit['_source']
        songs_data.append(SongResponse(
            id=hit['_id'],  # Use Elasticsearch document ID
            title=song_doc.get("title", ""),
            artist=song_doc.get("artist", ""),
            album=song_doc.get("album", ""),
            duration=song_doc.get("duration", 0),
            spotify_id=song_doc.get("spotify_id"),
            youtube_url=song_doc.get("youtube_url"),
            file_path=song_doc.get("file_path"),
            thumbnail_url=get_thumbnail_url(song_doc),
            download_status="completed",
            created_at=song_doc.get("created_at")
        ))
    
    return songs_data

@router.get("/local/by-artist/{artist_name}", response_model=List[SongResponse])
async def search_by_artist(
    artist_name: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search downloaded songs by artist name using Elasticsearch"""
    
    es_service = ElasticsearchService()
    
    # Build Elasticsearch query for artist search
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "match": {
                            "artist": {
                                "query": artist_name,
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                ]
            }
        },
        "size": limit
    }
    
    results = await es_service.search_raw(query)
    
    songs_data = []
    for hit in results.get('hits', {}).get('hits', []):
        song_doc = hit['_source']
        songs_data.append(SongResponse(
            id=hit['_id'],  # Use Elasticsearch document ID
            title=song_doc.get("title", ""),
            artist=song_doc.get("artist", ""),
            album=song_doc.get("album", ""),
            duration=song_doc.get("duration", 0),
            spotify_id=song_doc.get("spotify_id"),
            youtube_url=song_doc.get("youtube_url"),
            file_path=song_doc.get("file_path"),
            thumbnail_url=get_thumbnail_url(song_doc),
            download_status="completed",
            created_at=song_doc.get("created_at")
        ))
    
    return songs_data
