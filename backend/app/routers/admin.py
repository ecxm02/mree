"""Admin endpoints for system management"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models.user import User
from ..routers.auth import get_current_user
from ..services.simple_storage_service import SimpleStorageService

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/cleanup")
async def cleanup_old_songs(
    current_user: User = Depends(get_current_user)
):
    """Clean up songs that haven't been played in 6 months"""
    try:
        storage_service = SimpleStorageService()
        
        # Get stats before cleanup
        stats_before = await storage_service.get_storage_stats()
        
        # Run cleanup
        cleanup_result = await storage_service.cleanup_orphaned_files()
        
        # Get stats after cleanup
        stats_after = await storage_service.get_storage_stats()
        
        return {
            "message": "Cleanup completed successfully",
            "cleanup_result": cleanup_result,
            "before": {
                "total_songs": stats_before["total_songs"],
                "total_size_mb": stats_before["total_size_mb"]
            },
            "after": {
                "total_songs": stats_after["total_songs"],
                "total_size_mb": stats_after["total_size_mb"]
            },
            "savings": {
                "songs_removed": cleanup_result["files_removed"],
                "mb_freed": cleanup_result["mb_freed"]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")

@router.get("/storage-stats")
async def get_storage_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get overall storage statistics"""
    try:
        storage_service = SimpleStorageService()
        stats = await storage_service.get_storage_stats()
        
        return {
            "total_songs": stats["total_songs"],
            "total_size_mb": stats["total_size_mb"],
            "total_size_gb": round(stats["total_size_mb"] / 1024, 2),
            "active_users": stats["active_users"],
            "avg_songs_per_user": round(stats["avg_songs_per_user"], 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get storage stats: {str(e)}")

@router.get("/my-library-stats")
async def get_my_library_stats(
    current_user: User = Depends(get_current_user)
):
    """Get current user's library statistics"""
    try:
        storage_service = SimpleStorageService()
        stats = await storage_service.get_user_library_stats(current_user.id)
        
        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "song_count": stats["song_count"],
            "total_size_mb": stats["total_size_mb"],
            "total_size_gb": round(stats["total_size_mb"] / 1024, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get library stats: {str(e)}")
