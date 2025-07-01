from pydantic_settings import BaseSettings
from typing import List
import secrets
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://musicuser:musicpass@localhost:5433/musicdb"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9201"
    
    # Spotify API
    SPOTIFY_CLIENT_ID: str = ""
    SPOTIFY_CLIENT_SECRET: str = ""
    
    # JWT - Generate secure key if not provided
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Security
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # File storage paths - configurable for different drives
    MUSIC_STORAGE_PATH: str = os.getenv("MUSIC_STORAGE_PATH", "/mnt/hdd/mree/music")
    IMAGE_STORAGE_PATH: str = os.getenv("IMAGE_STORAGE_PATH", "/mnt/hdd/mree/images")
    MUSIC_DOWNLOAD_PATH: str = os.getenv("MUSIC_DOWNLOAD_PATH", "/mnt/hdd/mree/downloads")
    
    # Database storage paths - configurable for SSD
    POSTGRES_DATA_PATH: str = os.getenv("POSTGRES_DATA_PATH", "/mnt/ssd/mree/postgres")
    ELASTICSEARCH_DATA_PATH: str = os.getenv("ELASTICSEARCH_DATA_PATH", "/mnt/ssd/mree/elasticsearch")
    REDIS_DATA_PATH: str = os.getenv("REDIS_DATA_PATH", "/mnt/ssd/mree/redis")
    
    # Backup configuration
    BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
    BACKUP_PATH: str = os.getenv("BACKUP_PATH", "/mnt/backup/mree")
    BACKUP_SCHEDULE_HOUR: int = int(os.getenv("BACKUP_SCHEDULE_HOUR", "3"))  # 3 AM daily
    BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
    BACKUP_COMPRESS: bool = os.getenv("BACKUP_COMPRESS", "true").lower() == "true"
    
    # Cleanup configuration
    IMAGE_CLEANUP_ENABLED: bool = os.getenv("IMAGE_CLEANUP_ENABLED", "true").lower() == "true"
    
    # Metrics configuration
    METRICS_ENABLED: bool = os.getenv("METRICS_ENABLED", "true").lower() == "true"
    METRICS_UPDATE_INTERVAL: int = int(os.getenv("METRICS_UPDATE_INTERVAL", "60"))
    
    # Server
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
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
    
    # Background job settings
    CELERY_BROKER_URL: str = "redis://localhost:6380/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6380/2"
    
    # Celery worker settings (future-proofing for Celery 6.0+)
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = int(os.getenv("CELERY_WORKER_PREFETCH_MULTIPLIER", "1"))
    CELERY_BROKER_CONNECTION_RETRY: bool = os.getenv("CELERY_BROKER_CONNECTION_RETRY", "true").lower() == "true"
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP: bool = os.getenv("CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP", "true").lower() == "true"
    CELERY_BROKER_CONNECTION_MAX_RETRIES: int = int(os.getenv("CELERY_BROKER_CONNECTION_MAX_RETRIES", "10"))
    
    # Download settings
    MAX_DOWNLOAD_SIZE_MB: int = 50
    DOWNLOAD_TIMEOUT_SECONDS: int = 300
    MAX_CONCURRENT_DOWNLOADS: int = 3
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = 5
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Validate critical settings on startup
if not settings.SPOTIFY_CLIENT_ID or not settings.SPOTIFY_CLIENT_SECRET:
    print("⚠️  WARNING: Spotify API credentials not configured")

if settings.SECRET_KEY == "your-super-secret-jwt-key":
    print("⚠️  WARNING: Using default JWT secret key - set SECRET_KEY environment variable")
