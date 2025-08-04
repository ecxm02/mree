# PowerShell script to reindex Elasticsearch with pinyin support
# Run this script from the backend directory

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "Elasticsearch Pinyin Reindexing Script" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "app\services\elasticsearch_service.py")) {
    Write-Host "❌ Error: Please run this script from the backend directory" -ForegroundColor Red
    Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Check if virtual environment is activated (optional but recommended)
Write-Host "🔍 Checking Python environment..." -ForegroundColor Yellow

# Check if required files exist
$required_files = @(
    "songs_pinyin_mapping.json",
    "reindex_with_pinyin.py",
    "app\services\elasticsearch_service.py"
)

foreach ($file in $required_files) {
    if (-not (Test-Path $file)) {
        Write-Host "❌ Required file missing: $file" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required files found" -ForegroundColor Green

# Check if Elasticsearch is running
Write-Host "🔍 Checking Elasticsearch connection..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:9200/_cluster/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Elasticsearch is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to Elasticsearch at http://localhost:9200" -ForegroundColor Red
    Write-Host "   Make sure Elasticsearch is running with Docker Compose" -ForegroundColor Yellow
    Write-Host "   Run: docker-compose up elasticsearch" -ForegroundColor Cyan
    exit 1
}

# Run the reindexing script
Write-Host "🚀 Starting reindexing process..." -ForegroundColor Cyan

try {
    python reindex_with_pinyin.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 Reindexing completed successfully!" -ForegroundColor Green
        Write-Host "🔍 Your Elasticsearch now supports pinyin search!" -ForegroundColor Green
        Write-Host "   Try searching for 'dao gao' to find Chinese songs like '祷告'" -ForegroundColor Cyan
    } else {
        Write-Host "`n💥 Reindexing failed!" -ForegroundColor Red
        Write-Host "   Check the error messages above for details" -ForegroundColor Yellow
    }
} catch {
    Write-Host "`n💥 Error running reindexing script: $_" -ForegroundColor Red
}

Write-Host "`nPress any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
