from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import settings

# Database setup
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Import all models to ensure they're registered
from .models.user import User
from .models.song import Song
from .models.playlist import Playlist, PlaylistSong


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    lyrics = Column(Text)
    year = Column(Integer)
    genre = Column(String(100))
    album_art_url = Column(String(255))
    upload_user_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    uploader = relationship("User", back_populates="songs")
    favorites = relationship("UserFavorite", back_populates="song")


class Playlist(Base):
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_public = Column(Boolean, default=False)
    is_collaborative = Column(Boolean, default=False)
    cover_image_url = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="playlists")
    songs = relationship("PlaylistSong", back_populates="playlist")


class PlaylistSong(Base):
    __tablename__ = "playlist_songs"
    
    playlist_id = Column(Integer, ForeignKey("playlists.id"), primary_key=True)
    song_id = Column(Integer, ForeignKey("songs.id"), primary_key=True)
    position = Column(Integer, nullable=False)
    added_by_user_id = Column(Integer, ForeignKey("users.id"))
    added_at = Column(DateTime, default=func.now())
    
    # Relationships
    playlist = relationship("Playlist", back_populates="songs")
    song = relationship("Song")
    added_by = relationship("User")


class UserFavorite(Base):
    __tablename__ = "user_favorites"
    
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    song_id = Column(Integer, ForeignKey("songs.id"), primary_key=True)
    favorited_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="favorites")
    song = relationship("Song", back_populates="favorites")


class PlayHistory(Base):
    __tablename__ = "play_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False)
    played_at = Column(DateTime, default=func.now())
    play_duration_seconds = Column(Integer)
    completed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    song = relationship("Song")


class DownloadQueue(Base):
    __tablename__ = "download_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    query = Column(String(255), nullable=False)
    spotify_track_data = Column(Text)  # JSON data
    youtube_url = Column(String(255))
    status = Column(String(20), default="pending")  # pending, downloading, processing, completed, failed
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text)
    result_song_id = Column(Integer, ForeignKey("songs.id"))
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    result_song = relationship("Song")


# Database initialization
async def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
