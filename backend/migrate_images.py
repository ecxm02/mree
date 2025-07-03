#!/usr/bin/env python3
"""
Migration script to reorganize existing images into categorized directories
This script moves images from flat structure to prefix-based directory structure
"""
import os
import sys
from pathlib import Path
import shutil
import logging

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent))

from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_images():
    """Migrate images from flat structure to categorized structure"""
    image_path = Path(settings.IMAGE_STORAGE_PATH)
    
    if not image_path.exists():
        logger.info("Image storage path does not exist, nothing to migrate")
        return
    
    migrated_count = 0
    error_count = 0
    
    # Find all .jpg files in the root directory
    for image_file in image_path.glob("*.jpg"):
        try:
            # Extract spotify_id from filename
            spotify_id = image_file.stem
            
            if len(spotify_id) < 2:
                logger.warning(f"Skipping file with invalid name: {image_file}")
                continue
            
            # Create categorized directory
            prefix = spotify_id[:2]
            category_dir = image_path / prefix
            category_dir.mkdir(parents=True, exist_ok=True)
            
            # Move file to categorized directory
            destination = category_dir / image_file.name
            
            if destination.exists():
                logger.info(f"File already exists in destination: {destination}")
                # Remove the old file since it's duplicated
                image_file.unlink()
            else:
                shutil.move(str(image_file), str(destination))
                logger.info(f"Moved: {image_file} -> {destination}")
            
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"Error migrating {image_file}: {e}")
            error_count += 1
    
    logger.info(f"Migration complete: {migrated_count} files migrated, {error_count} errors")

if __name__ == "__main__":
    logger.info("Starting image directory migration...")
    migrate_images()
    logger.info("Migration finished")
