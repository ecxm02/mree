#!/bin/bash
# Complete Backend Reset Script
# This script will wipe ALL data and reset the backend to a clean state

echo "==========================================="
echo "🚨 COMPLETE BACKEND RESET SCRIPT 🚨"
echo "==========================================="
echo ""
echo "This will PERMANENTLY DELETE all:"
echo "  ✗ Music files (/mnt/8tbMain/mree/music/)"
echo "  ✗ Image files (/mnt/1tbSsd/mree/images/)"  
echo "  ✗ Download files (/mnt/8tbMain/mree/downloads/)"
echo "  ✗ PostgreSQL database (/mnt/1tbSsd/mree/postgres/)"
echo "  ✗ Elasticsearch data (/mnt/1tbSsd/mree/elasticsearch/)"
echo "  ✗ Redis data (/mnt/1tbSsd/mree/redis/)"
echo "  ✗ Backup files (/mnt/8tbMain/mree/backups/)"
echo ""
echo "Are you absolutely sure? This cannot be undone!"
read -p "Type 'RESET_EVERYTHING' to confirm: " confirm

if [ "$confirm" != "RESET_EVERYTHING" ]; then
    echo "❌ Reset cancelled."
    exit 1
fi

echo ""
echo "🛑 Stopping all containers..."
docker-compose down

echo ""
echo "🗑️  Removing Docker volumes and networks..."
docker-compose down --volumes --remove-orphans

echo ""
echo "🗑️  Deleting all data directories..."

# Music and media storage
sudo rm -rf /mnt/8tbMain/mree/music/*
sudo rm -rf /mnt/1tbSsd/mree/images/*
sudo rm -rf /mnt/8tbMain/mree/downloads/*

# Database storage  
sudo rm -rf /mnt/1tbSsd/mree/postgres/*
sudo rm -rf /mnt/1tbSsd/mree/elasticsearch/*
sudo rm -rf /mnt/1tbSsd/mree/redis/*

# Backup storage
sudo rm -rf /mnt/8tbMain/mree/backups/*

echo ""
echo "🏗️  Recreating directory structure..."

# Recreate base directories with proper permissions
sudo mkdir -p /mnt/8tbMain/mree/{music,downloads,backups}
sudo mkdir -p /mnt/1tbSsd/mree/{images,postgres,elasticsearch,redis}

# Set proper ownership (adjust user:group as needed)
sudo chown -R 1000:1000 /mnt/8tbMain/mree/
sudo chown -R 1000:1000 /mnt/1tbSsd/mree/

# Set proper permissions
sudo chmod -R 755 /mnt/8tbMain/mree/
sudo chmod -R 755 /mnt/1tbSsd/mree/

echo ""
echo "🔨 Rebuilding containers from scratch..."
docker-compose build --no-cache

echo ""
echo "✅ RESET COMPLETE!"
echo ""
echo "Your backend is now in a completely fresh state:"
echo "  ✓ All old data has been removed"
echo "  ✓ Fresh containers built with all fixes applied"
echo "  ✓ Ready for fresh startup"
echo ""
echo "To start the containers when ready, run:"
echo "  docker-compose up -d"
echo ""
echo "==========================================="
