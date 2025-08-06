from elasticsearch import Elasticsearch
from typing import Dict, List, Optional, Any
import json
import logging
from pathlib import Path
from datetime import datetime
import time
import random

from ..config import settings
from ..constants import SearchConfig

logger = logging.getLogger(__name__)

class ElasticsearchService:
    def __init__(self):
        """Initialize Elasticsearch client with connection retry logic"""
        self.es = None
        self.songs_index = "songs"
        self._connect_with_retry()
        
    def _connect_with_retry(self, max_retries=30, base_delay=1):
        """Connect to Elasticsearch with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                self.es = Elasticsearch(
                    [settings.ELASTICSEARCH_URL],
                    timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
                # Test the connection
                if self.es.ping():
                    logger.info(f"Successfully connected to Elasticsearch at {settings.ELASTICSEARCH_URL}")
                    return
                else:
                    raise ConnectionError("Elasticsearch ping failed")
                    
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to connect to Elasticsearch after {max_retries} attempts: {e}")
                    raise ConnectionError(f"Could not connect to Elasticsearch: {e}")
                
                # Calculate delay with jitter to avoid thundering herd
                delay = min(base_delay * (2 ** attempt), 60) + random.uniform(0, 1)
                logger.warning(f"Elasticsearch connection attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
    
    def _ensure_connected(self):
        """Ensure we have a valid Elasticsearch connection, reconnect if needed"""
        if self.es is None or not self.es.ping():
            logger.warning("Elasticsearch connection lost, attempting to reconnect...")
            self._connect_with_retry()
        
    async def ensure_index_exists(self):
        """Create songs index with pinyin analyzer, force recreate if mapping is wrong"""
        try:
            # Ensure we have a valid connection
            self._ensure_connected()
            
            # Check if index exists and has correct mapping
            if self.es.indices.exists(index=self.songs_index):
                current_mapping = self.es.indices.get_mapping(index=self.songs_index)
                title_mapping = current_mapping.get(self.songs_index, {}).get("mappings", {}).get("properties", {}).get("title", {})
                
                # If title field doesn't use pinyin_analyzer, recreate the index
                if title_mapping.get("analyzer") != "pinyin_analyzer":
                    logger.warning("Index exists but title field doesn't use pinyin_analyzer. Recreating index...")
                    self.es.indices.delete(index=self.songs_index)
                    # Fall through to create new index with pinyin mapping
                else:
                    logger.info("Index already exists with correct pinyin mapping")
                    return
            
            # Create index with pinyin analyzer (both for new index creation and recreation)
            logger.info(f"Creating new index '{self.songs_index}' with pinyin analyzer...")
            mapping = {
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "pinyin_analyzer": {
                                "tokenizer": "my_pinyin"
                            }
                        },
                        "tokenizer": {
                            "my_pinyin": {
                                "type": "pinyin",
                                "keep_first_letter": True,
                                "keep_separate_first_letter": False,
                                "keep_full_pinyin": True,
                                "keep_original": True,
                                "limit_first_letter_length": 16,
                                "lowercase": True,
                                "remove_duplicated_term": True
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "spotify_id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "pinyin_analyzer", "search_analyzer": "pinyin_analyzer"},
                        "artist": {"type": "text", "analyzer": "standard"},
                        "album": {"type": "text", "analyzer": "standard"},
                        "duration": {"type": "integer"},
                        "file_path": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "thumbnail_path": {"type": "keyword"},
                        "original_thumbnail_url": {"type": "keyword"},
                        "youtube_url": {"type": "keyword"},
                        "download_count": {"type": "integer"},
                        "download_status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "last_streamed": {"type": "date"}
                    }
                }
            }
            self.es.indices.create(index=self.songs_index, body=mapping)
            logger.info(f"Created Elasticsearch index with pinyin analyzer: {self.songs_index}")
            
        except Exception as e:
            logger.error(f"Error ensuring index exists: {e}")
            raise
    
    def ensure_index_exists_sync(self):
        """Synchronous version of ensure_index_exists for Celery tasks"""
        try:
            # Ensure we have a valid connection
            self._ensure_connected()
            
            # Check if index exists and has correct mapping
            if self.es.indices.exists(index=self.songs_index):
                current_mapping = self.es.indices.get_mapping(index=self.songs_index)
                title_mapping = current_mapping.get(self.songs_index, {}).get("mappings", {}).get("properties", {}).get("title", {})
                
                # If title field doesn't use pinyin_analyzer, recreate the index
                if title_mapping.get("analyzer") != "pinyin_analyzer":
                    logger.warning("Index exists but title field doesn't use pinyin_analyzer. Recreating index...")
                    self.es.indices.delete(index=self.songs_index)
                    # Fall through to create new index with pinyin mapping
                else:
                    logger.info("Index already exists with correct pinyin mapping")
                    return
            
            # Create index with pinyin analyzer (both for new index creation and recreation)
            logger.info(f"Creating new index '{self.songs_index}' with pinyin analyzer...")
            mapping = {
                "settings": {
                    "analysis": {
                        "analyzer": {
                            "pinyin_analyzer": {
                                "tokenizer": "my_pinyin"
                            }
                        },
                        "tokenizer": {
                            "my_pinyin": {
                                "type": "pinyin",
                                "keep_first_letter": True,
                                "keep_separate_first_letter": False,
                                "keep_full_pinyin": True,
                                "keep_original": True,
                                "limit_first_letter_length": 16,
                                "lowercase": True,
                                "remove_duplicated_term": True
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "spotify_id": {"type": "keyword"},
                        "title": {"type": "text", "analyzer": "pinyin_analyzer", "search_analyzer": "pinyin_analyzer"},
                        "artist": {"type": "text", "analyzer": "standard"},
                        "album": {"type": "text", "analyzer": "standard"},
                        "duration": {"type": "integer"},
                        "file_path": {"type": "keyword"},
                        "file_size": {"type": "long"},
                        "thumbnail_path": {"type": "keyword"},
                        "original_thumbnail_url": {"type": "keyword"},
                        "youtube_url": {"type": "keyword"},
                        "download_count": {"type": "integer"},
                        "download_status": {"type": "keyword"},
                        "created_at": {"type": "date"},
                        "updated_at": {"type": "date"},
                        "last_streamed": {"type": "date"}
                    }
                }
            }
            self.es.indices.create(index=self.songs_index, body=mapping)
            logger.info(f"Created Elasticsearch index with pinyin analyzer: {self.songs_index}")
            
        except Exception as e:
            logger.error(f"Error ensuring index exists (sync): {e}")
            raise
    
    async def add_song(self, song_data: Dict[str, Any]) -> bool:
        """Add or update a song in Elasticsearch"""
        try:
            # Ensure index exists with correct pinyin mapping
            await self.ensure_index_exists()
            
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
            self._ensure_connected()
            result = self.es.get(index=self.songs_index, id=spotify_id)
            return result["_source"]
        except Exception as e:
            logger.debug(f"Song not found in Elasticsearch: {spotify_id}")
            return None
    
    async def search_songs(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for songs in Elasticsearch with aggressive partial matching"""
        try:
            self._ensure_connected()
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
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
                "size": SearchConfig.DEFAULT_ELASTICSEARCH_SIZE,  # Configurable search limit
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
            self._ensure_connected()
            result = self.es.get(index=self.songs_index, id=spotify_id)
            return result["_source"]
        except Exception:
            return None
    
    def add_song_sync(self, song_data: Dict[str, Any]) -> bool:
        """Synchronous version of add_song for Celery tasks"""
        try:
            # Ensure index exists with correct pinyin mapping
            self.ensure_index_exists_sync()
            
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
        try:
            update_body = {
                "doc": {
                    "download_status": status,
                    "updated_at": datetime.utcnow().isoformat()
                },
                "upsert": {
                    "spotify_id": spotify_id,
                    "download_status": status,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
            self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body=update_body,
                refresh=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating song status (sync): {e}")
            return False
    
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
            self._ensure_connected()
            return self.es.search(index=self.songs_index, body=query)
        except Exception as e:
            logger.error(f"Error executing raw search: {e}")
            return {"hits": {"hits": []}}
    
    async def search_raw(self, query: Dict) -> Dict:
        """Execute raw Elasticsearch query (async for API endpoints)"""
        try:
            self._ensure_connected()
            return self.es.search(index=self.songs_index, body=query)
        except Exception as e:
            logger.error(f"Error executing raw search: {e}")
            return {"hits": {"hits": []}}
    
    def get_total_songs(self) -> int:
        """Get total number of songs in the catalog"""
        try:
            self._ensure_connected()
            result = self.es.count(index=self.songs_index)
            return result.get("count", 0)
        except Exception as e:
            logger.error(f"Error getting total song count: {e}")
            return 0
    
    async def update_song_status(self, spotify_id: str, status: str) -> bool:
        """Update the download status of a song"""
        try:
            update_body = {
                "doc": {
                    "download_status": status,
                    "updated_at": datetime.utcnow().isoformat()
                },
                "upsert": {
                    "spotify_id": spotify_id,
                    "download_status": status,
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
            
            response = self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body=update_body,
                refresh=True
            )
            
            logger.debug(f"Updated song status for {spotify_id}: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating song status for {spotify_id}: {e}")
            return False
    
    async def update_song(self, spotify_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a song document in Elasticsearch (async version)"""
        try:
            update_body = {
                "doc": update_data
            }
            
            response = self.es.update(
                index=self.songs_index,
                id=spotify_id,
                body=update_body,
                refresh=True
            )
            
            logger.debug(f"Updated song in Elasticsearch: {spotify_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating song in Elasticsearch: {e}")
            return False
