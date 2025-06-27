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

class UserLibrary(Base):
    """User's personal music library - lightweight references to songs"""
    __tablename__ = "user_libraries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    spotify_id = Column(String(100), nullable=False, index=True)  # Reference to song
    
    # User-specific metadata only
    is_favorite = Column(Boolean, default=False)
    play_count = Column(Integer, default=0)
    last_played = Column(DateTime(timezone=True))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="library")
    
    # Prevent duplicate entries: one user can't have same song twice
    __table_args__ = (
        UniqueConstraint('user_id', 'spotify_id', name='unique_user_song'),
    )

class DownloadQueue(Base):
    """Temporary queue for tracking downloads in progress"""
    __tablename__ = "download_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    spotify_id = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(Enum(DownloadStatus), default=DownloadStatus.PENDING)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    requester = relationship("User")