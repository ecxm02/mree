from elasticsearch import Elasticsearch
from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self):
        """Initialize Elasticsearch client"""
        self.es = Elasticsearch([settings.ELASTICSEARCH_URL])
        self.songs_index = "songs"
        
    async def ensure_index_exists(self):
        """Create songs index if it doesn't exist"""
        if not self.es.indices.exists(index=self.songs_index):
            mapping = {
                "mappings": {
                    "properties": {
                        "spotify_id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "standard"},
                        "artist": {"type": "text", "analyzer": "standard"},
                        "album": {"type": "text", "analyzer": "standard"},
                        "duration": {"type": "integer"},
                        "file_path": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "thumbnail_path": {"type": "keyword"},
                        "original_thumbnail_url": {"type": "keyword"},
                        "youtube_url": {"type": "keyword"},
                        "download_count": {"type": "integer"},
                        "download_status": {"type": "keyword"},  # pending, downloading, completed, failed
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "last_streamed": {"type": "date"}  # Track when song was last played
                    }
                }
            }
            self.es.indices.create(index=self.songs_index, body=mapping)
            logger.info(f"Created Elasticsearch index: {self.songs_index}")
    
    async def add_song(self, song_data: Dict[str, Any]) -> bool:
        """Add or update a song in Elasticsearch"""
        try:
            # Use spotify_id as document ID for uniqueness
            doc_id = song_data["spotify_id"]
            
            result = self.es.index(
                index=self.songs_index,
                id=doc_id,
                body=song_data
            )
            
            logger.info(f"Added song to Elasticsearch: {song_data['title']} by {song_data['artist']}")
            return result["result"] in ["created", "updated"]
            
        except Exception as e:
            logger.error(f"Error adding song to Elasticsearch: {e}")
            return False
    
    async def get_song(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """Get song by Spotify ID"""
        try:
            result = self.es.get(index=self.songs_index, id=spotify_id)
            return result["_source"]
        except Exception as e:
            logger.debug(f"Song not found in Elasticsearch: {spotify_id}")
            return None
    
    async def search_songs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for songs in Elasticsearch"""
        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "artist^1.5", "album"],
                        "type": "best_fields",
                        "fuzziness": "AUTO"
                    }
                },
                "size": limit,
                "sort": [
                    {"download_count": {"order": "desc"}},
                    "_score"
                ]
            }
            
            result = self.es.search(index=self.songs_index, body=search_body)
            return [hit["_source"] for hit in result["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Error searching Elasticsearch: {e}")
            return []
    
    async def song_exists(self, spotify_id: str) -> bool:
        """Check if song exists and is downloaded"""
        song = await self.get_song(spotify_id)
        if not song:
            return False
            
        # Check if file actually exists on disk
        file_path = Path(song.get("file_path", ""))
        return file_path.exists() and file_path.is_file()
    
    async def update_download_count(self, spotify_id: str) -> bool:
        """Increment download count for a song"""
        try:
            # Use update API to increment counter
            update_body = {
                "script": {
                    "source": "ctx._source.download_count = (ctx._source.download_count ?: 0) + 1",
                    "lang": "painless"
                }
            }
            
            result = self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body=update_body
            )
            
            return result["result"] == "updated"
            
        except Exception as e:
            logger.error(f"Error updating download count: {e}")
            return False
    
    async def get_popular_songs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get most popular songs by download count"""
        try:
            search_body = {
                "query": {"match_all": {}},
                "sort": [{"download_count": {"order": "desc"}}],
                "size": limit
            }
            
            result = self.es.search(index=self.songs_index, body=search_body)
            return [hit["_source"] for hit in result["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Error getting popular songs: {e}")
            return []
    
    async def update_last_streamed(self, spotify_id: str) -> bool:
        """Update the last_streamed timestamp when a song is played"""
        try:
            # Update only the last_streamed field
            update_body = {
                "doc": {
                    "last_streamed": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
            result = self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body=update_body
            )
            
            logger.debug(f"Updated last_streamed for song: {spotify_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating last_streamed for {spotify_id}: {e}")
            return False

    async def get_all_songs(self) -> List[Dict[str, Any]]:
        """Get all songs from Elasticsearch for cleanup operations"""
        try:
            search_body = {
                "query": {"match_all": {}},
                "size": 10000,  # Adjust based on your expected song count
                "_source": ["spotify_id", "file_path", "file_size", "created_at", "last_streamed"]
            }
            
            result = self.es.search(index=self.songs_index, body=search_body)
            return [hit["_source"] for hit in result["hits"]["hits"]]
            
        except Exception as e:
            logger.error(f"Error getting all songs: {e}")
            return []
    
    def get_file_path(self, spotify_id: str) -> str:
        """Generate standardized file path for a song using configurable storage path"""
        # Organize by first 2 characters of spotify_id for better file system distribution
        prefix = spotify_id[:2]
        from ..config import settings
        return f"{settings.MUSIC_STORAGE_PATH}/{prefix}/{spotify_id}.mp3"
    
    # Synchronous methods for Celery tasks (Celery can't handle async)
    
    def get_song_sync(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous version of get_song for Celery tasks"""
        try:
            result = self.es.get(index=self.songs_index, id=spotify_id)
            return result["_source"]
        except Exception:
            return None
    
    def add_song_sync(self, song_data: Dict[str, Any]) -> bool:
        """Synchronous version of add_song for Celery tasks"""
        try:
            doc_id = song_data["spotify_id"]
            result = self.es.index(
                index=self.songs_index,
                id=doc_id,
                body=song_data,
                refresh=True  # Make immediately searchable
            )
            logger.info(f"Added song to Elasticsearch: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding song to Elasticsearch: {e}")
            return False
    
    def update_song_sync(self, spotify_id: str, update_data: Dict[str, Any]) -> bool:
        """Synchronous version of update_song for Celery tasks"""
        try:
            result = self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body={"doc": update_data},
                refresh=True
            )
            logger.info(f"Updated song in Elasticsearch: {spotify_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating song in Elasticsearch: {e}")
            return False
    
    def update_song_status_sync(self, spotify_id: str, status: str) -> bool:
        """Synchronous version of update_song_status for Celery tasks"""
        return self.update_song_sync(spotify_id, {
            "download_status": status,
            "updated_at": datetime.utcnow().isoformat()
        })
    
    def increment_download_count_sync(self, spotify_id: str) -> bool:
        """Synchronous version of increment_download_count for Celery tasks"""
        try:
            # Use update script to atomically increment download count
            result = self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body={
                    "script": {
                        "source": "ctx._source.download_count = (ctx._source.download_count ?: 0) + 1; ctx._source.updated_at = params.timestamp",
                        "params": {"timestamp": datetime.utcnow().isoformat()}
                    }
                },
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"Error incrementing download count: {e}")
            return False
    
    def search_raw_sync(self, query: Dict) -> Dict:
        """Execute raw Elasticsearch query (synchronous for Celery tasks)"""
        try:
            return self.es.search(index=self.songs_index, body=query)
        except Exception as e:
            logger.error(f"Error executing raw search: {e}")
            return {"hits": {"hits": []}}
    
    async def search_raw(self, query: Dict) -> Dict:
        """Execute raw Elasticsearch query (async for API endpoints)"""
        try:
            return self.es.search(index=self.songs_index, body=query)
        except Exception as e:
            logger.error(f"Error executing raw search: {e}")
            return {"hits": {"hits": []}}
    
    def get_total_songs(self) -> int:
        """Get total number of songs in the catalog"""
        try:
            result = self.es.count(index=self.songs_index)
            return result.get("count", 0)
        except Exception as e:
            logger.error(f"Error getting total song count: {e}")
            return 0
