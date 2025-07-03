#!/bin/bash
# Complete Backend Reset Script
# This script will wipe ALL data and reset the backend to a clean state

# Function to load environment variables from .env file
load_env() {
    if [ -f ".env" ]; then
        export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
        echo "✅ Environment variables loaded from .env file"
    else
        echo "❌ .env file not found! Please make sure you're in the backend directory."
        exit 1
    fi
}

# Function to validate required environment variables
validate_env() {
    local required_vars=(
        "MUSIC_STORAGE_PATH"
        "IMAGE_STORAGE_PATH"
        "MUSIC_DOWNLOAD_PATH"
        "POSTGRES_DATA_PATH"
        "ELASTICSEARCH_DATA_PATH"
        "REDIS_DATA_PATH"
        "BACKUP_PATH"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "❌ Required environment variable $var is not set!"
            exit 1
        fi
    done
    echo "✅ All required environment variables are set"
}

# Load and validate environment
load_env
validate_env

echo "==========================================="
echo "🚨 COMPLETE BACKEND RESET SCRIPT 🚨"
echo "==========================================="
echo ""
echo "This will PERMANENTLY DELETE all:"
echo "  ✗ Music files ($MUSIC_STORAGE_PATH)"
echo "  ✗ Image files ($IMAGE_STORAGE_PATH)"  
echo "  ✗ Download files ($MUSIC_DOWNLOAD_PATH)"
echo "  ✗ PostgreSQL database ($POSTGRES_DATA_PATH)"
echo "  ✗ Elasticsearch data ($ELASTICSEARCH_DATA_PATH)"
echo "  ✗ Redis data ($REDIS_DATA_PATH)"
echo "  ✗ Backup files ($BACKUP_PATH)"
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
echo "  🗑️  Clearing music storage: $MUSIC_STORAGE_PATH"
sudo rm -rf "$MUSIC_STORAGE_PATH"/*

echo "  🗑️  Clearing image storage: $IMAGE_STORAGE_PATH"
sudo rm -rf "$IMAGE_STORAGE_PATH"/*

echo "  🗑️  Clearing download storage: $MUSIC_DOWNLOAD_PATH"
sudo rm -rf "$MUSIC_DOWNLOAD_PATH"/*

# Database storage  
echo "  🗑️  Clearing PostgreSQL data: $POSTGRES_DATA_PATH"
sudo rm -rf "$POSTGRES_DATA_PATH"/*

echo "  🗑️  Clearing Elasticsearch data: $ELASTICSEARCH_DATA_PATH"
sudo rm -rf "$ELASTICSEARCH_DATA_PATH"/*

echo "  🗑️  Clearing Redis data: $REDIS_DATA_PATH"
sudo rm -rf "$REDIS_DATA_PATH"/*

# Backup storage
echo "  🗑️  Clearing backup storage: $BACKUP_PATH"
sudo rm -rf "$BACKUP_PATH"/*

echo ""
echo "🏗️  Recreating directory structure..."

# Function to create directory with proper permissions
create_directory() {
    local dir_path="$1"
    echo "  📁 Creating directory: $dir_path"
    sudo mkdir -p "$dir_path"
    sudo chown -R 1000:1000 "$dir_path"
    sudo chmod -R 755 "$dir_path"
}

# Recreate all directories
create_directory "$MUSIC_STORAGE_PATH"
create_directory "$IMAGE_STORAGE_PATH"
create_directory "$MUSIC_DOWNLOAD_PATH"
create_directory "$POSTGRES_DATA_PATH"
create_directory "$ELASTICSEARCH_DATA_PATH"
create_directory "$REDIS_DATA_PATH"
create_directory "$BACKUP_PATH"

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
echo "Directory structure recreated:"
echo "  📁 Music storage: $MUSIC_STORAGE_PATH"
echo "  📁 Image storage: $IMAGE_STORAGE_PATH"
echo "  📁 Download storage: $MUSIC_DOWNLOAD_PATH"
echo "  📁 PostgreSQL data: $POSTGRES_DATA_PATH"
echo "  📁 Elasticsearch data: $ELASTICSEARCH_DATA_PATH"
echo "  📁 Redis data: $REDIS_DATA_PATH"
echo "  📁 Backup storage: $BACKUP_PATH"
echo ""
echo "To start the containers when ready, run:"
echo "  docker-compose up -d"
echo ""
echo "==========================================="
