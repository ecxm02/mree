from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(
        extra='ignore',
        env_file=".env",
        case_sensitive=True
    )
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # Elasticsearch
    ELASTICSEARCH_URL: str
    
    # Spotify API
    SPOTIFY_CLIENT_ID: str
    SPOTIFY_CLIENT_SECRET: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://100.67.83.60:8000", "*"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "100.67.83.60", "*"]
    
    # File storage paths
    MUSIC_STORAGE_PATH: str
    IMAGE_STORAGE_PATH: str
    MUSIC_DOWNLOAD_PATH: str
    
    # Database storage paths
    POSTGRES_DATA_PATH: str
    ELASTICSEARCH_DATA_PATH: str
    REDIS_DATA_PATH: str
    
    # Backup configuration
    BACKUP_ENABLED: bool
    BACKUP_PATH: str
    BACKUP_SCHEDULE_HOUR: int
    BACKUP_RETENTION_DAYS: int
    BACKUP_COMPRESS: bool
    
    # Cleanup configuration
    IMAGE_CLEANUP_ENABLED: bool
    
    # Metrics configuration
    METRICS_ENABLED: bool
    METRICS_UPDATE_INTERVAL: int
    
    # Server
    DEBUG: bool
    HOST: str
    PORT: int
    WORKERS: int = 1
    
    # Rate limiting (requests per time window)
    RATE_LIMIT_SEARCH: int = 60  # per minute
    RATE_LIMIT_DOWNLOAD: int = 10  # per minute
    RATE_LIMIT_AUTH: int = 5  # per 5 minutes
    RATE_LIMIT_REGISTER: int = 3  # per hour
    
    # Audio settings
    DEFAULT_AUDIO_QUALITY: int = 320
    SUPPORTED_FORMATS: List[str] = ["mp3", "flac", "ogg"]
    
    # User storage quotas (in MB)
    DEFAULT_USER_QUOTA_MB: int = 1000
    MAX_USER_QUOTA_MB: int = 10000
    
    # Background job settings - These are defaults, actual values come from REDIS_URL
    CELERY_BROKER_URL: str = "redis://music-redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://music-redis:6379/2"
    
    # Celery worker settings
    CELERY_WORKER_PREFETCH_MULTIPLIER: int
    CELERY_BROKER_CONNECTION_RETRY: bool
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: bool
    CELERY_BROKER_CONNECTION_MAX_RETRIES: int
    
    # Download settings
    MAX_DOWNLOAD_SIZE_MB: int = 50
    DOWNLOAD_TIMEOUT_SECONDS: int = 300
    MAX_CONCURRENT_DOWNLOADS: int = 3
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


settings = Settings()

# Validate critical settings on startup
if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
    print("⚠️  WARNING: Spotify API credentials not configured")

if settings.SECRET_KEY == "your-super-secret-jwt-key":
    print("⚠️  WARNING: Using default JWT secret key - set SECRET_KEY environment variable")
