#!/usr/bin/env python3
"""
Reindex all existing songs with the new pinyin mapping.

This script will:
1. Backup existing songs data
2. Delete the old index
3. Create a new index with pinyin analyzer
4. Reindex all songs with the new mapping

Run this script after updating your Elasticsearch to support pinyin.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Set up Django/FastAPI-style imports
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.elasticsearch_service import ElasticsearchService
from app.config import settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ElasticsearchReindexer:
    """Handle reindexing of Elasticsearch with pinyin support"""
    
    def __init__(self):
        self.es_service = ElasticsearchService()
        
        # Use configured backup path or fallback to current directory
        backup_dir = Path(getattr(settings, 'BACKUP_PATH', '.'))
        backup_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        
        backup_filename = f"songs_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.backup_file = backup_dir / backup_filename
        
        logger.info(f"📁 Backup will be saved to: {self.backup_file}")
        logger.info(f"🔧 Using backup directory: {backup_dir}")
        
    def backup_existing_songs(self) -> List[Dict[str, Any]]:
        """Backup all existing songs before reindexing"""
        logger.info("Starting backup of existing songs...")
        
        try:
            # Get all songs using the raw search
            query = {
                "query": {"match_all": {}},
                "size": 10000,  # Adjust if you have more than 10k songs
                "_source": True
            }
            
            result = self.es_service.search_raw_sync(query)
            songs = []
            
            for hit in result.get('hits', {}).get('hits', []):
                song_data = hit['_source']
                song_data['_id'] = hit['_id']  # Preserve original ID
                songs.append(song_data)
            
            # Save to backup file
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(songs, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Backed up {len(songs)} songs to {self.backup_file}")
            return songs
            
        except Exception as e:
            logger.error(f"❌ Failed to backup songs: {e}")
            raise
    
    def delete_old_index(self):
        """Delete the existing songs index"""
        logger.info("Deleting old index...")
        
        try:
            if self.es_service.es.indices.exists(index=self.es_service.songs_index):
                self.es_service.es.indices.delete(index=self.es_service.songs_index)
                logger.info("✅ Old index deleted")
            else:
                logger.info("ℹ️ Index doesn't exist, nothing to delete")
                
        except Exception as e:
            logger.error(f"❌ Failed to delete old index: {e}")
            raise
    
    def create_new_index(self):
        """Create new index with pinyin mapping"""
        logger.info("Creating new index with pinyin analyzer...")
        
        try:
            # Load the pinyin mapping from the JSON file
            mapping_file = Path(__file__).parent / "songs_pinyin_mapping.json"
            if not mapping_file.exists():
                logger.error(f"❌ Mapping file not found: {mapping_file}")
                raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
            
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            
            # Create the index
            self.es_service.es.indices.create(
                index=self.es_service.songs_index, 
                body=mapping
            )
            logger.info("✅ New index created with pinyin analyzer")
            
        except Exception as e:
            logger.error(f"❌ Failed to create new index: {e}")
            raise
    
    def reindex_songs(self, songs: List[Dict[str, Any]]):
        """Reindex all songs with the new mapping"""
        logger.info(f"Reindexing {len(songs)} songs...")
        
        successful = 0
        failed = 0
        
        for i, song in enumerate(songs):
            try:
                # Remove metadata fields that shouldn't be reindexed
                song_data = song.copy()
                song_id = song_data.pop('_id', song_data.get('spotify_id'))
                
                # Use the synchronous add method
                if self.es_service.add_song_sync(song_data):
                    successful += 1
                else:
                    failed += 1
                    logger.warning(f"Failed to reindex song: {song_id}")
                
                # Progress indicator
                if (i + 1) % 50 == 0:
                    logger.info(f"Progress: {i + 1}/{len(songs)} songs processed")
                    
            except Exception as e:
                failed += 1
                logger.error(f"Error reindexing song {song.get('spotify_id', 'unknown')}: {e}")
        
        logger.info(f"✅ Reindexing complete: {successful} successful, {failed} failed")
        
        if failed > 0:
            logger.warning(f"⚠️ {failed} songs failed to reindex. Check logs for details.")
    
    def verify_reindex(self, original_count: int):
        """Verify that reindexing was successful"""
        logger.info("Verifying reindex results...")
        
        try:
            # Get total count in new index
            new_count = self.es_service.get_total_songs()
            
            logger.info(f"Original songs: {original_count}")
            logger.info(f"Reindexed songs: {new_count}")
            
            if new_count >= original_count * 0.95:  # Allow 5% loss for cleanup
                logger.info("✅ Reindexing verification successful")
                
                # Test pinyin search
                logger.info("Testing pinyin search functionality...")
                
                # Search for a common Chinese character pattern
                test_query = {
                    "query": {
                        "match": {
                            "title": {
                                "query": "dao gao",
                                "analyzer": "pinyin_analyzer"
                            }
                        }
                    },
                    "size": 5
                }
                
                result = self.es_service.search_raw_sync(test_query)
                hits = result.get('hits', {}).get('hits', [])
                
                if hits:
                    logger.info(f"✅ Pinyin search test successful: found {len(hits)} results")
                    for hit in hits:
                        title = hit['_source'].get('title', 'Unknown')
                        logger.info(f"  - {title}")
                else:
                    logger.warning("⚠️ Pinyin search test returned no results (this might be normal if you have no Chinese songs)")
                
                return True
            else:
                logger.error(f"❌ Reindexing verification failed: significant data loss detected")
                return False
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    def run_reindex(self):
        """Run the complete reindexing process"""
        logger.info("🚀 Starting Elasticsearch reindexing with pinyin support...")
        
        try:
            # Step 1: Backup existing data
            songs = self.backup_existing_songs()
            original_count = len(songs)
            
            if original_count == 0:
                logger.info("ℹ️ No songs found to reindex. Creating new index anyway...")
                self.delete_old_index()
                self.create_new_index()
                logger.info("✅ Empty index created with pinyin support")
                return True
            
            # Step 2: Delete old index
            self.delete_old_index()
            
            # Step 3: Create new index with pinyin
            self.create_new_index()
            
            # Step 4: Reindex all songs
            self.reindex_songs(songs)
            
            # Step 5: Verify results
            if self.verify_reindex(original_count):
                logger.info("🎉 Reindexing completed successfully!")
                logger.info(f"📁 Backup saved as: {self.backup_file}")
                return True
            else:
                logger.error("💥 Reindexing verification failed!")
                return False
                
        except Exception as e:
            logger.error(f"💥 Reindexing failed: {e}")
            logger.info(f"🔄 You can restore from backup: {self.backup_file}")
            return False

def main():
    """Main entry point"""
    print("=" * 60)
    print("Elasticsearch Reindexing with Pinyin Support")
    print("=" * 60)
    
    reindexer = ElasticsearchReindexer()
    
    # Ask for confirmation
    print("\n⚠️  WARNING: This will delete and recreate your Elasticsearch index!")
    print(f"📁 A backup will be created: {reindexer.backup_file}")
    
    confirm = input("\nDo you want to continue? (yes/no): ").lower().strip()
    
    if confirm not in ['yes', 'y']:
        print("❌ Reindexing cancelled by user")
        return False
    
    # Run the reindexing process
    success = reindexer.run_reindex()
    
    if success:
        print("\n🎉 SUCCESS: Your Elasticsearch index now supports pinyin search!")
        print("🔍 You can now search for Chinese songs using pinyin (e.g., 'dao gao' for '祷告')")
    else:
        print(f"\n💥 FAILED: Reindexing failed. Check the backup file: {reindexer.backup_file}")
    
    return success

if __name__ == "__main__":
    main()
