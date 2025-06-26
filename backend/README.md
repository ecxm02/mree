# 🎵 Music Streaming Backend - Raspberry Pi Deployment

This backend provides a complete music streaming API with Spotify integration and YouTube downloads.

## 🚀 Quick Start on Raspberry Pi

### Method 1: Using PowerShell (from Windows)

1. **From your Windows machine (in the mree directory):**
   ```powershell
   cd backend
   .\deploy-to-pi.ps1 -PiIP "192.168.1.100"
   ```
   Replace `192.168.1.100` with your Pi's IP address.

2. **SSH to your Pi and run the deployment:**
   ```bash
   ssh pi@192.168.1.100
   cd /home/pi/mree-backend
   chmod +x deploy.sh
   ./deploy.sh
   ```

### Method 2: Manual Copy

1. **Copy files to your Pi** (using WinSCP, git, or USB):
   ```bash
   # Transfer the backend folder to your Pi
   ```

2. **On your Raspberry Pi:**
   ```bash
   cd /path/to/backend
   chmod +x deploy.sh
   ./deploy.sh
   ```

## ⚙️ Configuration

1. **Edit the environment file:**
   ```bash
   nano .env
   ```

2. **Required settings:**
   - `SPOTIFY_CLIENT_ID` - Get from [Spotify Developer Dashboard](https://developer.spotify.com/)
   - `SPOTIFY_CLIENT_SECRET` - From Spotify Developer Dashboard
   - `JWT_SECRET_KEY` - Generate a secure random string
   - Database passwords (optional, defaults are fine for local use)

## 🧪 Testing

After deployment, test your API:

```bash
# Health check
curl http://localhost:8000/health

# API documentation
curl http://localhost:8000/docs
```

## 🌐 Access from Flutter App

Update your Flutter app configuration to use:
```
http://YOUR_PI_IP:8000
```

## 📊 Monitoring

```bash
# View logs
docker-compose logs -f app

# Check status
docker-compose ps

# Restart services
docker-compose restart
```

## 🔧 Troubleshooting

### Services not starting:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Port conflicts:
The services use these ports:
- FastAPI: 8000
- PostgreSQL: 5433
- Redis: 6380
- Elasticsearch: 9201

Make sure these ports are available on your Pi.

### Spotify API errors:
1. Verify your Spotify credentials in `.env`
2. Check that your Spotify app settings allow the redirect URIs

## 📱 Flutter Integration

Once the backend is running, you can connect your Flutter app by updating the base URL in your Flutter project to point to your Pi's IP address.

Example Flutter configuration:
```dart
const String baseUrl = 'http://192.168.1.100:8000/api';
```
