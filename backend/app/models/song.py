from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base

class UserLibrary(Base):
    """User's personal music library - references to songs they 'own' by Spotify ID"""
    __tablename__ = "user_libraries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    spotify_id = Column(String(100), nullable=False, index=True)  # Reference to Elasticsearch
    
    # When user added this song to their library
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # User-specific metadata
    is_favorite = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    last_played = Column(DateTime(timezone=True))
    
    # Ensure user can't add same song twice
    __table_args__ = (UniqueConstraint('user_id', 'spotify_id', name='unique_user_song'),)
    
    # Relationships
    user = relationship("User", back_populates="library")

class Playlist(Base):
    """User playlists"""
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(500))
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="playlists")
    songs = relationship("PlaylistSong", back_populates="playlist", cascade="all, delete-orphan")

class PlaylistSong(Base):
    """Songs in playlists - references Elasticsearch by Spotify ID"""
    __tablename__ = "playlist_songs"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    spotify_id = Column(String(100), nullable=False, index=True)  # Reference to Elasticsearch
    position = Column(Integer, nullable=False)  # Order in playlist
    
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    playlist = relationship("Playlist", back_populates="songs")