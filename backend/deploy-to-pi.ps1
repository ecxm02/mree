# PowerShell script to deploy backend to Raspberry Pi
# Run this from Windows to copy files to your Pi

param(
    [Parameter(Mandatory=$true)]
    [string]$PiIP,
    
    [Parameter(Mandatory=$false)]
    [string]$PiUser = "pi",
    
    [Parameter(Mandatory=$false)]
    [string]$PiPath = "/home/pi/mree-backend"
)

Write-Host "🚀 Deploying Music Streaming Backend to Raspberry Pi..." -ForegroundColor Green
Write-Host "📍 Target: ${PiUser}@${PiIP}:${PiPath}" -ForegroundColor Cyan

# Check if backend directory exists
if (-not (Test-Path ".\backend")) {
    Write-Host "❌ Backend directory not found!" -ForegroundColor Red
    Write-Host "📁 Make sure you're running this from the mree project root" -ForegroundColor Yellow
    exit 1
}

# Use SCP to copy files (requires OpenSSH or Git Bash)
Write-Host "📦 Copying files to Raspberry Pi..." -ForegroundColor Yellow

try {
    # Copy the entire backend directory
    scp -r .\backend\ "${PiUser}@${PiIP}:${PiPath}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Files copied successfully!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "🔧 Now run these commands on your Raspberry Pi:" -ForegroundColor Cyan
        Write-Host "   ssh $PiUser@$PiIP" -ForegroundColor White
        Write-Host "   cd $PiPath" -ForegroundColor White
        Write-Host "   chmod +x deploy.sh" -ForegroundColor White
        Write-Host "   ./deploy.sh" -ForegroundColor White
        Write-Host ""
        Write-Host "📝 Don't forget to:" -ForegroundColor Yellow
        Write-Host "   1. Edit .env file with your Spotify credentials" -ForegroundColor White
        Write-Host "   2. Set a secure JWT secret key" -ForegroundColor White
        Write-Host "   3. Update database passwords if needed" -ForegroundColor White
        Write-Host ""
        Write-Host "🌐 After deployment, your API will be available at:" -ForegroundColor Green
        Write-Host "   http://${PiIP}:8000/docs" -ForegroundColor White
    } else {
        Write-Host "❌ Failed to copy files!" -ForegroundColor Red
        Write-Host "💡 Make sure SSH is enabled on your Pi and you can connect:" -ForegroundColor Yellow
        Write-Host "   ssh $PiUser@$PiIP" -ForegroundColor White
    }
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Alternative methods:" -ForegroundColor Yellow
    Write-Host "   1. Use WinSCP to copy the backend folder" -ForegroundColor White
    Write-Host "   2. Use git to push/pull the code" -ForegroundColor White
    Write-Host "   3. Use a USB drive to transfer files" -ForegroundColor White
}
