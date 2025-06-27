from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from ..database import Base

class DownloadStatus(enum.Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"

class Song(Base):
    """Global song storage - one copy per unique track"""
    __tablename__ = "songs"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    artist = Column(String(200), nullable=False, index=True)
    album = Column(String(200))
    duration = Column(Integer)  # in seconds
    spotify_id = Column(String(100), unique=True, index=True, nullable=False)  # Made unique!
    youtube_url = Column(Text)
    file_path = Column(Text)  # Single file path for all users
    thumbnail_url = Column(Text)
    download_status = Column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
    
    # Remove user_id - songs are global now!
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # REMOVED
    
    # Track download info
    first_requested_by = Column(Integer, ForeignKey("users.id"))  # Who first requested it
    download_count = Column(Integer, default=0)  # How many users have it
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_libraries = relationship("UserLibrary", back_populates="song")
    first_requester = relationship("User", foreign_keys=[first_requested_by])

class UserLibrary(Base):
    """User's personal music library - references to songs they 'own'"""
    __tablename__ = "user_libraries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    
    # User-specific metadata
    is_favorite = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    last_played = Column(DateTime(timezone=True))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="library")
    song = relationship("Song", back_populates="user_libraries")
    
    # Ensure each user can only have one copy of each song
    __table_args__ = (
        UniqueConstraint('user_id', 'song_id', name='unique_user_song'),
    )
