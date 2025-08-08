# Deployment Guide (Linux / Raspberry Pi)

## Prerequisites on Raspberry Pi
1. Docker and Docker Compose installed
2. Git installed
3. Ports 8000, 5433, 6380, 9201 available

## Deployment Steps

### 1. Clone or copy the project to your Pi
```bash
# If using git
git clone <your-repo-url>
cd mree/backend

# Or copy files via SCP/FTP
```

### 2. Create environment file
```bash
cp .env.example .env
# Edit .env with your actual values
```

### 3. Build and start services
```bash
# Build images
docker-compose build

# Start all services (PostgreSQL, Redis, Elasticsearch, FastAPI)
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 4. Initialize the database
```bash
# Initialize database tables
docker-compose exec music-api python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Test the API
```bash
# Check API health
curl http://localhost:8000/health

# Check API docs
# Open http://your-pi-ip:8000/docs in browser
```

## Accessing from Flutter App
Update your Flutter app to point to: `http://your-pi-ip:8000`

## Useful Commands
```bash
# View logs
docker-compose logs -f music-api

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update code and restart
docker-compose down
docker-compose build
docker-compose up -d
```
