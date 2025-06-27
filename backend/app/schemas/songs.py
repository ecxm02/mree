from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime

from ..utils.validation import validate_spotify_id, sanitize_search_query

class SongBase(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    spotify_id: Optional[str] = None
    youtube_url: Optional[str] = None
    
    @validator('spotify_id')
    def validate_spotify_id_format(cls, v):
        if v is not None:
            return validate_spotify_id(v)
        return v

class SongCreate(SongBase):
    pass

class SongResponse(SongBase):
    id: int
    file_path: Optional[str]
    thumbnail_url: Optional[str]
    download_status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SongSearch(BaseModel):
    query: str
    limit: Optional[int] = 10
    
    @validator('query')
    def validate_search_query(cls, v):
        return sanitize_search_query(v)
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None:
            if v < 1:
                raise ValueError("Limit must be at least 1")
            if v > 50:
                raise ValueError("Limit cannot exceed 50")
        return v

class DownloadRequest(BaseModel):
    spotify_id: str
    
    @validator('spotify_id')
    def validate_spotify_id_format(cls, v):
        return validate_spotify_id(v)

class SpotifySearchResult(BaseModel):
    spotify_id: str
    title: str
    artist: str
    album: str
    duration: int
    preview_url: Optional[str]
    thumbnail_url: Optional[str]

class SearchResponse(BaseModel):
    results: List[SpotifySearchResult]
    total: int
