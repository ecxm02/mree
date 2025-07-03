"""
Application constants and default values
Centralizes all hardcoded values for easy configuration
"""

class AudioConfig:
    """Audio processing configuration"""
    DEFAULT_QUALITY = 192
    SUPPORTED_QUALITIES = [128, 192, 256, 320]
    DEFAULT_FORMAT = "mp3"
    SUPPORTED_FORMATS = ["mp3", "flac", "ogg", "wav"]
    CHUNK_SIZE = 8192

class SearchConfig:
    """Search and query configuration"""
    DEFAULT_SEARCH_LIMIT = 50
    MAX_SEARCH_LIMIT = 10000
    DEFAULT_ELASTICSEARCH_SIZE = 10000
    
class UserConfig:
    """User-related configuration"""
    DEFAULT_QUOTA_MB = 1000
    MAX_QUOTA_MB = 10000
    
class AppConfig:
    """Application metadata"""
    VERSION = "1.0.0"
    NAME = "MREE Music Streaming"
    DESCRIPTION = "Music streaming with YouTube downloads and Spotify metadata"
    
class NetworkConfig:
    """Network and connectivity configuration"""
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 3
    DEFAULT_CHUNK_SIZE = 8192
    
class RateLimitConfig:
    """Rate limiting configuration"""
    SEARCH_REQUESTS_PER_MINUTE = 60
    DOWNLOAD_REQUESTS_PER_MINUTE = 10
    AUTH_REQUESTS_PER_5_MINUTES = 5
    REGISTER_REQUESTS_PER_HOUR = 3
