from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..database import get_db
from ..models.user import User
from ..models.song import UserLibrary
from ..schemas.songs import SongSearch, SearchResponse, SpotifySearchResult, SongResponse
from ..routers.auth import get_current_user
from ..services.spotify_service import SpotifyService
from ..services.elasticsearch_service import ElasticsearchService
from ..services.image_service import ImageService
from ..tasks import download_song
from ..constants import SearchConfig

logger = logging.getLogger(__name__)

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
            id=0,  # Use 0 for Elasticsearch results (no database ID yet)
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
    """Search downloaded songs with aggressive partial matching using multiple strategies"""
    
    es_service = ElasticsearchService()
    
    # Strategy 1: Multi-match query with pinyin support for Chinese titles
    multi_match_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "multi_match": {
                            "query": search.query,
                            "fields": [
                                f"title^{SearchConfig.TITLE_BOOST}", 
                                f"artist^{SearchConfig.ARTIST_BOOST}", 
                                f"album^{SearchConfig.ALBUM_BOOST}"
                            ],
                            "type": "best_fields",
                            "fuzziness": SearchConfig.FUZZY_FUZZINESS,
                            "prefix_length": SearchConfig.FUZZY_PREFIX_LENGTH,
                            "max_expansions": SearchConfig.FUZZY_MAX_EXPANSIONS,
                            "minimum_should_match": SearchConfig.MINIMUM_SHOULD_MATCH,
                            "tie_breaker": SearchConfig.TIE_BREAKER
                        }
                    }
                ]
            }
        },
        "size": search.limit
    }
    
    # Strategy 2: Direct pinyin match for Chinese text
    pinyin_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "match": {
                            "title": {
                                "query": search.query,
                                "analyzer": "pinyin_analyzer"
                            }
                        }
                    }
                ]
            }
        },
        "size": search.limit
    }
    
    # Strategy 2: Wildcard query for very partial matches (e.g., "per*" matches "perfect")
    wildcard_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "bool": {
                            "should": [
                                {"wildcard": {"title": f"*{search.query.lower()}*"}},
                                {"wildcard": {"artist": f"*{search.query.lower()}*"}},
                                {"wildcard": {"album": f"*{search.query.lower()}*"}}
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        },
        "size": search.limit
    }
    
    # Strategy 3: Prefix query for "starts with" matching
    prefix_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "bool": {
                            "should": [
                                {"prefix": {"title": search.query.lower()}},
                                {"prefix": {"artist": search.query.lower()}},
                                {"prefix": {"album": search.query.lower()}}
                            ],
                            "minimum_should_match": 1
                        }
                    }
                ]
            }
        },
        "size": search.limit
    }
    
    # Strategy 4: N-gram query for partial word matching
    ngram_query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "bool": {
                            "should": [
                                {
                                    "match": {
                                        "title": {
                                            "query": search.query,
                                            "analyzer": "standard",
                                            "minimum_should_match": "1"
                                        }
                                    }
                                },
                                {
                                    "match": {
                                        "artist": {
                                            "query": search.query,
                                            "analyzer": "standard",
                                            "minimum_should_match": "1"
                                        }
                                    }
                                },
                                {
                                    "match": {
                                        "album": {
                                            "query": search.query,
                                            "analyzer": "standard",
                                            "minimum_should_match": "1"
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        },
        "size": search.limit
    }
    
    # Execute all strategies and combine results
    all_results = []
    seen_spotify_ids = set()
    
    # Execute queries in order of precision (best results first)
    queries = [
        ("multi_match", multi_match_query),
        ("pinyin", pinyin_query),
        ("prefix", prefix_query),
        ("wildcard", wildcard_query),
        ("ngram", ngram_query)
    ]
    
    for strategy_name, query in queries:
        try:
            results = await es_service.search_raw(query)
            for hit in results.get('hits', {}).get('hits', []):
                song_doc = hit['_source']
                spotify_id = song_doc.get("spotify_id")
                
                # Avoid duplicates
                if spotify_id not in seen_spotify_ids:
                    seen_spotify_ids.add(spotify_id)
                    song_response = SongResponse(
                        id=0,  # Use 0 for Elasticsearch results
                        title=song_doc.get("title", ""),
                        artist=song_doc.get("artist", ""),
                        album=song_doc.get("album", ""),
                        duration=song_doc.get("duration", 0),
                        spotify_id=spotify_id,
                        youtube_url=song_doc.get("youtube_url"),
                        file_path=song_doc.get("file_path"),
                        thumbnail_url=get_thumbnail_url(song_doc),
                        download_status="completed",
                        created_at=song_doc.get("created_at")
                    )
                    all_results.append(song_response)
                    
                    # Stop when we have enough results
                    if len(all_results) >= search.limit:
                        break
        except Exception as e:
            logger.warning(f"Search strategy '{strategy_name}' failed: {e}")
            continue
        
        # Stop if we have enough results
        if len(all_results) >= search.limit:
            break
    
    return all_results[:search.limit]

@router.get("/local/by-artist/{artist_name}", response_model=List[SongResponse])
async def search_by_artist(
    artist_name: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search downloaded songs by artist name with aggressive partial matching"""
    
    es_service = ElasticsearchService()
    
    # Build Elasticsearch query for artist search with multiple strategies
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"download_status": "completed"}},
                    {
                        "bool": {
                            "should": [
                                # Exact fuzzy match
                                {
                                    "match": {
                                        "artist": {
                                            "query": artist_name,
                                            "fuzziness": SearchConfig.FUZZY_FUZZINESS,
                                            "prefix_length": SearchConfig.FUZZY_PREFIX_LENGTH,
                                            "max_expansions": SearchConfig.FUZZY_MAX_EXPANSIONS
                                        }
                                    }
                                },
                                # Wildcard match for partial queries
                                {"wildcard": {"artist": f"*{artist_name.lower()}*"}},
                                # Prefix match
                                {"prefix": {"artist": artist_name.lower()}}
                            ],
                            "minimum_should_match": 1
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
            id=0,  # Use 0 for Elasticsearch results (no database ID yet)
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
