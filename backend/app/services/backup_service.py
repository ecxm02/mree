"""Database backup service for PostgreSQL and Elasticsearch"""
import os
import shutil
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import asyncio

from ..config import settings

logger = logging.getLogger(__name__)

class BackupService:
    """Service for backing up databases and managing backup retention"""
    
    def __init__(self):
        self.backup_base_path = Path(settings.BACKUP_PATH)
        self.postgres_data_path = Path(settings.POSTGRES_DATA_PATH)
        self.elasticsearch_data_path = Path(settings.ELASTICSEARCH_DATA_PATH)
        self.redis_data_path = Path(settings.REDIS_DATA_PATH)
        
        # Ensure backup directory exists
        self.backup_base_path.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> Dict[str, Any]:
        """Create a full backup of all databases"""
        if not settings.BACKUP_ENABLED:
            logger.info("Backup is disabled in configuration")
            return {"status": "disabled", "message": "Backup is disabled"}
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_base_path / f"backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        results = {
            "timestamp": timestamp,
            "backup_path": str(backup_dir),
            "postgres": {"status": "skipped"},
            "elasticsearch": {"status": "skipped"},
            "redis": {"status": "skipped"}
        }
        
        try:
            # Backup PostgreSQL
            postgres_result = self._backup_postgres(backup_dir)
            results["postgres"] = postgres_result
            
            # Backup Elasticsearch
            elasticsearch_result = self._backup_elasticsearch(backup_dir)
            results["elasticsearch"] = elasticsearch_result
            
            # Backup Redis
            redis_result = self._backup_redis(backup_dir)
            results["redis"] = redis_result
            
            # Create backup metadata
            self._create_backup_metadata(backup_dir, results)
            
            # Compress backup if enabled
            if settings.BACKUP_COMPRESS:
                compressed_file = self._compress_backup(backup_dir)
                results["compressed_file"] = str(compressed_file)
                # Remove uncompressed directory
                shutil.rmtree(backup_dir)
            
            logger.info(f"Backup completed successfully: {backup_dir}")
            results["status"] = "success"
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
            
            # Cleanup failed backup
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
        
        return results
    
    def _backup_postgres(self, backup_dir: Path) -> Dict[str, Any]:
        """Backup PostgreSQL database using pg_dump"""
        try:
            postgres_backup_dir = backup_dir / "postgres"
            postgres_backup_dir.mkdir(exist_ok=True)
            
            # Use Docker to run pg_dump
            dump_file = postgres_backup_dir / "database_dump.sql"
            
            cmd = [
                "docker", "exec", "mree-music-db-1",  # Adjust container name as needed
                "pg_dump", "-U", "musicuser", "-d", "musicdb",
                "--no-password", "--verbose"
            ]
            
            logger.info("Starting PostgreSQL backup...")
            with open(dump_file, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                # Also copy data directory if accessible
                if self.postgres_data_path.exists():
                    data_backup_dir = postgres_backup_dir / "data"
                    shutil.copytree(self.postgres_data_path, data_backup_dir, dirs_exist_ok=True)
                
                size_mb = dump_file.stat().st_size / (1024 * 1024)
                logger.info(f"PostgreSQL backup completed: {size_mb:.2f} MB")
                return {
                    "status": "success",
                    "size_mb": round(size_mb, 2),
                    "dump_file": str(dump_file)
                }
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                return {
                    "status": "error",
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"PostgreSQL backup error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _backup_elasticsearch(self, backup_dir: Path) -> Dict[str, Any]:
        """Backup Elasticsearch data directory"""
        try:
            es_backup_dir = backup_dir / "elasticsearch"
            es_backup_dir.mkdir(exist_ok=True)
            
            if not self.elasticsearch_data_path.exists():
                return {"status": "error", "error": "Elasticsearch data path not found"}
            
            logger.info("Starting Elasticsearch backup...")
            
            # Copy Elasticsearch data directory
            data_backup_dir = es_backup_dir / "data"
            shutil.copytree(self.elasticsearch_data_path, data_backup_dir, dirs_exist_ok=True)
            
            # Calculate backup size
            total_size = sum(f.stat().st_size for f in data_backup_dir.rglob('*') if f.is_file())
            size_mb = total_size / (1024 * 1024)
            
            logger.info(f"Elasticsearch backup completed: {size_mb:.2f} MB")
            return {
                "status": "success",
                "size_mb": round(size_mb, 2),
                "data_dir": str(data_backup_dir)
            }
            
        except Exception as e:
            logger.error(f"Elasticsearch backup error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _backup_redis(self, backup_dir: Path) -> Dict[str, Any]:
        """Backup Redis data"""
        try:
            redis_backup_dir = backup_dir / "redis"
            redis_backup_dir.mkdir(exist_ok=True)
            
            # Use Docker to create Redis backup
            cmd = [
                "docker", "exec", "mree-redis-1",  # Adjust container name as needed
                "redis-cli", "BGSAVE"
            ]
            
            logger.info("Starting Redis backup...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Copy Redis data directory if accessible
                if self.redis_data_path.exists():
                    data_backup_dir = redis_backup_dir / "data"
                    shutil.copytree(self.redis_data_path, data_backup_dir, dirs_exist_ok=True)
                    
                    total_size = sum(f.stat().st_size for f in data_backup_dir.rglob('*') if f.is_file())
                    size_mb = total_size / (1024 * 1024)
                    
                    logger.info(f"Redis backup completed: {size_mb:.2f} MB")
                    return {
                        "status": "success",
                        "size_mb": round(size_mb, 2),
                        "data_dir": str(data_backup_dir)
                    }
                else:
                    return {"status": "success", "size_mb": 0, "note": "Redis data path not accessible"}
            else:
                logger.error(f"Redis backup failed: {result.stderr}")
                return {"status": "error", "error": result.stderr}
                
        except Exception as e:
            logger.error(f"Redis backup error: {e}")
            return {"status": "error", "error": str(e)}
    
    def _create_backup_metadata(self, backup_dir: Path, results: Dict[str, Any]):
        """Create metadata file for the backup"""
        metadata = {
            "backup_date": datetime.now().isoformat(),
            "version": "1.0",
            "backup_results": results,
            "config": {
                "postgres_data_path": str(self.postgres_data_path),
                "elasticsearch_data_path": str(self.elasticsearch_data_path),
                "redis_data_path": str(self.redis_data_path),
                "compression_enabled": settings.BACKUP_COMPRESS
            }
        }
        
        metadata_file = backup_dir / "backup_metadata.json"
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _compress_backup(self, backup_dir: Path) -> Path:
        """Compress backup directory"""
        logger.info(f"Compressing backup: {backup_dir}")
        
        compressed_file = backup_dir.with_suffix('.tar.gz')
        
        cmd = [
            "tar", "-czf", str(compressed_file),
            "-C", str(backup_dir.parent),
            backup_dir.name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Compression failed: {result.stderr}")
        
        logger.info(f"Backup compressed to: {compressed_file}")
        return compressed_file
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Remove old backups based on retention policy"""
        if not settings.BACKUP_ENABLED:
            return {"status": "disabled", "message": "Backup is disabled"}
        
        cutoff_date = datetime.now() - timedelta(days=settings.BACKUP_RETENTION_DAYS)
        deleted_count = 0
        freed_space_mb = 0
        
        try:
            for backup_path in self.backup_base_path.glob("backup_*"):
                if backup_path.is_dir() or backup_path.suffix == '.tar.gz':
                    # Extract date from backup name
                    try:
                        backup_date_str = backup_path.stem.split('_', 1)[1][:8]  # YYYYMMDD
                        backup_date = datetime.strptime(backup_date_str, "%Y%m%d")
                        
                        if backup_date < cutoff_date:
                            # Calculate size before deletion
                            if backup_path.is_dir():
                                size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                            else:
                                size = backup_path.stat().st_size
                            
                            freed_space_mb += size / (1024 * 1024)
                            
                            # Delete old backup
                            if backup_path.is_dir():
                                shutil.rmtree(backup_path)
                            else:
                                backup_path.unlink()
                            
                            deleted_count += 1
                            logger.info(f"Deleted old backup: {backup_path}")
                            
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse backup date from: {backup_path}")
                        continue
            
            return {
                "status": "success",
                "deleted_count": deleted_count,
                "freed_space_mb": round(freed_space_mb, 2),
                "retention_days": settings.BACKUP_RETENTION_DAYS
            }
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def list_backups(self) -> Dict[str, Any]:
        """List all available backups"""
        backups = []
        total_size_mb = 0
        
        try:
            for backup_path in sorted(self.backup_base_path.glob("backup_*")):
                if backup_path.is_dir() or backup_path.suffix == '.tar.gz':
                    # Calculate size
                    if backup_path.is_dir():
                        size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
                    else:
                        size = backup_path.stat().st_size
                    
                    size_mb = size / (1024 * 1024)
                    total_size_mb += size_mb
                    
                    # Extract date from backup name
                    try:
                        backup_date_str = backup_path.stem.split('_', 1)[1]
                        backup_date = datetime.strptime(backup_date_str, "%Y%m%d_%H%M%S")
                        
                        backups.append({
                            "name": backup_path.name,
                            "path": str(backup_path),
                            "date": backup_date.isoformat(),
                            "size_mb": round(size_mb, 2),
                            "compressed": backup_path.suffix == '.tar.gz'
                        })
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse backup date from: {backup_path}")
                        continue
            
            return {
                "status": "success",
                "backups": backups,
                "total_count": len(backups),
                "total_size_mb": round(total_size_mb, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return {"status": "error", "error": str(e)}

# Global backup service instance
backup_service = BackupService()
