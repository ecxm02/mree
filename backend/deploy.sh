#!/bin/bash

# Deployment script for Raspberry Pi
echo "🚀 Deploying Music Streaming Backend to Raspberry Pi..."

# Check if we're on the Pi
if [[ $(uname -m) != "aarch64" && $(uname -m) != "armv7l" ]]; then
    echo "⚠️  This script should be run on the Raspberry Pi"
    echo "📋 Copy the backend folder to your Pi first:"
    echo "   scp -r ./backend pi@your-pi-ip:/home/pi/mree-backend"
    echo "   ssh pi@your-pi-ip"
    echo "   cd /home/pi/mree-backend"
    echo "   chmod +x deploy.sh"
    echo "   ./deploy.sh"
    exit 1
fi

# Create required directories
echo "📁 Creating storage directories..."
sudo mkdir -p /opt/mree/music
sudo mkdir -p /opt/mree/images
sudo mkdir -p /opt/mree/logs
sudo chown -R $USER:$USER /opt/mree

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your actual values:"
    echo "   - Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET"
    echo "   - Update database passwords"
    echo "   - Set SECRET_KEY for JWT"
    echo ""
    echo "📝 Edit the file: nano .env"
    echo "Press any key to continue after editing..."
    read -n 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in, then run this script again."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo pip3 install docker-compose
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔧 Building and starting services..."
docker-compose build --no-cache
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# Check service status
echo "📊 Checking service status..."
docker-compose ps

# Initialize database
echo "🗄️  Initializing database..."
docker-compose exec -T app python -c "
from app.database import init_db
import asyncio
asyncio.run(init_db())
print('✅ Database initialized successfully')
"

# Test API
echo "🧪 Testing API..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is responding!"
    echo ""
    echo "🎉 Deployment successful!"
    echo ""
    echo "🌐 API Documentation: http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo "🔍 API Health Check: http://$(hostname -I | awk '{print $1}'):8000/health"
    echo ""
    echo "📱 Update your Flutter app to use: http://$(hostname -I | awk '{print $1}'):8000"
else
    echo "❌ API is not responding. Check logs:"
    echo "   docker-compose logs app"
fi

echo ""
echo "📝 Useful commands:"
echo "   View logs: docker-compose logs -f app"
echo "   Restart: docker-compose restart"
echo "   Stop: docker-compose down"
echo "   Update: git pull && docker-compose build && docker-compose up -d"
