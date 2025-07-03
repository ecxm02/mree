"""Image service for downloading and managing album artwork"""
import os
import requests
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import hashlib

from ..config import settings
from ..constants import AudioConfig

logger = logging.getLogger(__name__)

class ImageService:
    def __init__(self):
        """Initialize image service"""
        self.image_path = Path(settings.IMAGE_STORAGE_PATH)
        self.image_path.mkdir(parents=True, exist_ok=True)
        
    def download_album_art(self, spotify_id: str, image_url: str) -> Optional[str]:
        """
        Download album artwork and return local file path
        
        Args:
            spotify_id: Spotify track ID for naming
            image_url: Original Spotify image URL
            
        Returns:
            Local file path if successful, None if failed
        """
        if not image_url:
            return None
            
        try:
            # Create categorized directory structure (same as music files)
            prefix = spotify_id[:2]
            category_dir = self.image_path / prefix
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename based on spotify_id
            filename = f"{spotify_id}.jpg"
            local_path = category_dir / filename
            
            # Skip if already exists
            if local_path.exists() and local_path.stat().st_size > 0:
                logger.debug(f"Album art already exists: {local_path}")
                return str(local_path)
            
            # Download the image
            logger.info(f"Downloading album art: {image_url}")
            response = requests.get(image_url, timeout=30, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"Invalid content type for image: {content_type}")
                return None
            
            # Save the image
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=AudioConfig.CHUNK_SIZE):
                    f.write(chunk)
            
            # Verify file was created and has content
            if local_path.exists() and local_path.stat().st_size > 0:
                logger.info(f"Successfully downloaded album art: {local_path}")
                return str(local_path)
            else:
                logger.error(f"Downloaded file is empty or missing: {local_path}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to download album art from {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading album art: {e}")
            return None
    
    def get_image_url(self, spotify_id: str) -> Optional[str]:
        """
        Get the local image URL for serving via API
        
        Args:
            spotify_id: Spotify track ID
            
        Returns:
            API URL path for the image, or None if not found
        """
        prefix = spotify_id[:2]
        category_dir = self.image_path / prefix
        filename = f"{spotify_id}.jpg"
        local_path = category_dir / filename
        
        if local_path.exists() and local_path.stat().st_size > 0:
            return f"/api/images/albums/{filename}"
        
        return None
    
    def get_image_url_with_fallback(self, spotify_id: str, original_url: str = None) -> str:
        """
        Get image URL with automatic failsafe - downloads if missing
        
        Args:
            spotify_id: Spotify track ID
            original_url: Original Spotify image URL for re-download
            
        Returns:
            Local API URL if available, original URL as fallback
        """
        prefix = spotify_id[:2]
        category_dir = self.image_path / prefix
        filename = f"{spotify_id}.jpg"
        local_path = category_dir / filename
        
        # Check if local file exists and is valid
        if local_path.exists() and local_path.stat().st_size > 0:
            return f"/api/images/albums/{filename}"
        
        # File missing or corrupted - try to re-download if we have original URL
        if original_url:
            logger.warning(f"Local image missing for {spotify_id}, attempting re-download")
            downloaded_path = self.download_album_art(spotify_id, original_url)
            
            if downloaded_path:
                logger.info(f"Successfully re-downloaded missing image for {spotify_id}")
                return f"/api/images/albums/{filename}"
            else:
                logger.error(f"Failed to re-download image for {spotify_id}")
        
        # Return original URL as final fallback
        return original_url if original_url else None
    
    def verify_and_repair_image(self, spotify_id: str, original_url: str = None) -> bool:
        """
        Verify image exists and is valid, repair if necessary
        
        Args:
            spotify_id: Spotify track ID
            original_url: Original Spotify image URL for repair
            
        Returns:
            True if image is available (local or repaired), False otherwise
        """
        prefix = spotify_id[:2]
        category_dir = self.image_path / prefix
        filename = f"{spotify_id}.jpg"
        local_path = category_dir / filename
        
        # Check if file exists and is valid
        if local_path.exists() and local_path.stat().st_size > 0:
            return True
        
        # Try to repair by re-downloading
        if original_url:
            logger.info(f"Repairing missing/corrupted image for {spotify_id}")
            downloaded_path = self.download_album_art(spotify_id, original_url)
            return downloaded_path is not None
        
        return False
    
    def cleanup_unused_images(self, active_spotify_ids: list) -> dict:
        """
        Remove album art files that are no longer referenced
        
        Args:
            active_spotify_ids: List of spotify IDs that should be kept
            
        Returns:
            Cleanup statistics
        """
        try:
            deleted_count = 0
            freed_space = 0
            
            # Get all image files from all subdirectories
            for prefix_dir in self.image_path.iterdir():
                if prefix_dir.is_dir():
                    for image_file in prefix_dir.glob("*.jpg"):
                        # Extract spotify_id from filename
                        spotify_id = image_file.stem
                        
                        if spotify_id not in active_spotify_ids:
                            file_size = image_file.stat().st_size
                            image_file.unlink()
                            deleted_count += 1
                            freed_space += file_size
                            logger.info(f"Deleted unused album art: {image_file}")
                    
                    # Remove empty directories
                    if not any(prefix_dir.iterdir()):
                        prefix_dir.rmdir()
                        logger.info(f"Removed empty directory: {prefix_dir}")
            
            return {
                "status": "success",
                "deleted_count": deleted_count,
                "freed_space_mb": round(freed_space / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Error during image cleanup: {e}")
            return {"status": "error", "error": str(e)}
