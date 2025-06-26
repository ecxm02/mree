from elasticsearch import Elasticsearch
from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path

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
                        "thumbnail_url": {"type": "keyword"},
                        "youtube_url": {"type": "keyword"},
                        "download_count": {"type": "integer"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"}
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
    
    def get_file_path(self, spotify_id: str) -> str:
        """Generate standardized file path for a song"""
        # Organize by first 2 characters of spotify_id for better file system distribution
        prefix = spotify_id[:2]
        return f"/app/music/{prefix}/{spotify_id}.mp3"
