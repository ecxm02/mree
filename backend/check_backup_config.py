#!/usr/bin/env python3
"""
Check backup configuration for the reindexing script.
This script shows where backups will be saved based on your .env settings.
"""

import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_backup_config():
    """Check and display backup configuration"""
    print("=" * 60)
    print("Backup Configuration Check")
    print("=" * 60)
    
    try:
        from app.config import settings
        
        # Check if BACKUP_PATH is configured
        backup_path = getattr(settings, 'BACKUP_PATH', None)
        
        if backup_path:
            backup_dir = Path(backup_path)
            print(f"✅ BACKUP_PATH configured: {backup_dir}")
            
            # Check if directory exists
            if backup_dir.exists():
                print(f"✅ Backup directory exists: {backup_dir}")
                
                # Check if directory is writable
                try:
                    test_file = backup_dir / "test_write.tmp"
                    test_file.write_text("test")
                    test_file.unlink()
                    print(f"✅ Backup directory is writable")
                except Exception as e:
                    print(f"❌ Backup directory is not writable: {e}")
                    print(f"   Please check permissions for: {backup_dir}")
            else:
                print(f"⚠️ Backup directory doesn't exist (will be created): {backup_dir}")
        else:
            print(f"⚠️ BACKUP_PATH not configured in .env")
            print(f"   Backup will be saved to current directory: {Path.cwd()}")
        
        # Show other backup-related settings
        print(f"\n📋 Other backup settings:")
        backup_enabled = getattr(settings, 'BACKUP_ENABLED', 'Not set')
        backup_retention = getattr(settings, 'BACKUP_RETENTION_DAYS', 'Not set')
        backup_compress = getattr(settings, 'BACKUP_COMPRESS', 'Not set')
        
        print(f"   BACKUP_ENABLED: {backup_enabled}")
        print(f"   BACKUP_RETENTION_DAYS: {backup_retention}")
        print(f"   BACKUP_COMPRESS: {backup_compress}")
        
        # Show where the reindex backup will be saved
        from datetime import datetime
        backup_filename = f"songs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        if backup_path:
            full_backup_path = Path(backup_path) / backup_filename
        else:
            full_backup_path = Path.cwd() / backup_filename
            
        print(f"\n🎯 Reindex backup will be saved as:")
        print(f"   {full_backup_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        print(f"   Make sure you're in the backend directory and .env file exists")
        return False

def show_env_example():
    """Show example .env configuration for backup"""
    print(f"\n💡 Example .env configuration:")
    print(f"   # Backup configuration")
    print(f"   BACKUP_PATH=C:/mree/backups")
    print(f"   BACKUP_ENABLED=true")
    print(f"   BACKUP_RETENTION_DAYS=30")
    print(f"   BACKUP_COMPRESS=true")
    print(f"")
    print(f"   # Or use a relative path:")
    print(f"   BACKUP_PATH=./backups")

if __name__ == "__main__":
    success = check_backup_config()
    
    if not success:
        show_env_example()
    
    print(f"\n" + "=" * 60)
