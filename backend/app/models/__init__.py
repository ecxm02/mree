# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .song import UserLibrary, Playlist, PlaylistSong, DownloadStatus

__all__ = [
    "User",
    "UserLibrary", 
    "Playlist",
    "PlaylistSong",
    "DownloadStatus"
]