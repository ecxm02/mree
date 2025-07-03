"""Router for serving album artwork images"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

from ..config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])

@router.get("/albums/{filename}")
async def get_album_art(filename: str):
    """
    Serve album artwork files
    
    Args:
        filename: Image filename (e.g., "4uLU6hMCjMI75M1A2tKUQC.jpg")
    """
    try:
        # Validate filename (security)
        if not filename.endswith('.jpg') or '/' in filename or '\\' in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Extract spotify_id for categorized lookup
        spotify_id = filename.replace('.jpg', '')
        if len(spotify_id) < 2:
            raise HTTPException(status_code=400, detail="Invalid filename format")
        
        # Construct categorized file path
        prefix = spotify_id[:2]
        image_path = Path(settings.IMAGE_STORAGE_PATH) / prefix / filename
        
        # Check if file exists
        if not image_path.exists() or not image_path.is_file():
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Return the file
        return FileResponse(
            path=str(image_path),
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"}  # Cache for 24 hours
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving image {filename}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
