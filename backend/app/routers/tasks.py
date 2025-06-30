from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..database import get_db
from ..models.user import User
from ..routers.auth import get_current_user
from ..worker import celery_app

router = APIRouter(prefix="/tasks", tags=["tasks"])
logger = logging.getLogger(__name__)

@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get the status of a background task"""
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed"
            }
        elif task.state == "PROGRESS":
            return {
                "task_id": task_id,
                "status": "progress",
                "progress": task.info.get("progress", 0),
                "message": task.info.get("message", "Processing...")
            }
        elif task.state == "SUCCESS":
            return {
                "task_id": task_id,
                "status": "completed",
                "result": task.result
            }
        elif task.state == "FAILURE":
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(task.info)
            }
        else:
            return {
                "task_id": task_id,
                "status": task.state.lower(),
                "message": "Task is being processed"
            }
            
    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Cancel a background task"""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {
            "task_id": task_id,
            "message": "Task cancellation requested"
        }
        
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")

@router.get("/")
async def get_active_tasks(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get all active tasks (admin only feature could be added later)"""
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        return {
            "active_tasks": active_tasks or {},
            "message": "Active tasks retrieved"
        }
        
    except Exception as e:
        logger.error(f"Error getting active tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active tasks")
