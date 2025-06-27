from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database import Base

# Association table for playlist-song many-to-many relationship
playlist_songs = Table(
    'playlist_songs',
    Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id'), primary_key=True),
    Column('song_id', Integer, ForeignKey('songs.id'), primary_key=True),
    Column('position', Integer, default=0),  # Order in playlist
    Column('added_at', DateTime(timezone=True), server_default=func.now())
)

class Playlist(Base):
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    
    # User who created this playlist
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="playlists")
    songs = relationship("Song", secondary=playlist_songs, backref="playlists")

class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    position = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    playlist = relationship("Playlist")
    song = relationship("Song", back_populates="playlist_songs")
