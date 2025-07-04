# Flutter Clean Script for Windows
# This script fixes permission issues and cleans Flutter build artifacts

param(
    [switch]$Deep,
    [switch]$Run,
    [switch]$EnableDeveloperMode
)

Write-Host "Flutter Clean Script for Windows" -ForegroundColor Green
Write-Host "=====================================" 

# Navigate to project directory
$projectPath = Split-Path $MyInvocation.MyCommand.Path
Set-Location $projectPath

# Function to check and enable Developer Mode
function Enable-DeveloperMode {
    Write-Host "Checking Developer Mode status..." -ForegroundColor Yellow
    
    $devModeKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock"
    
    try {
        $allowDevelopmentWithoutDevLicense = Get-ItemProperty -Path $devModeKey -Name "AllowDevelopmentWithoutDevLicense" -ErrorAction SilentlyContinue
        
        if ($allowDevelopmentWithoutDevLicense.AllowDevelopmentWithoutDevLicense -eq 1) {
            Write-Host "Developer Mode is already enabled!" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "Developer Mode is not enabled. Attempting to enable..." -ForegroundColor Yellow
            
            # Try to enable Developer Mode via registry
            try {
                Set-ItemProperty -Path $devModeKey -Name "AllowDevelopmentWithoutDevLicense" -Value 1 -Force
                Write-Host "Developer Mode enabled successfully!" -ForegroundColor Green
                return $true
            }
            catch {
                Write-Host "Failed to enable Developer Mode automatically. Please enable it manually:" -ForegroundColor Red
                Write-Host "1. Press Win+I to open Settings" -ForegroundColor Yellow
                Write-Host "2. Go to Update & Security > For developers" -ForegroundColor Yellow
                Write-Host "3. Turn on Developer Mode" -ForegroundColor Yellow
                Write-Host "Or run: start ms-settings:developers" -ForegroundColor Yellow
                return $false
            }
        }
    }
    catch {
        Write-Host "Unable to check Developer Mode status. Manual check required." -ForegroundColor Yellow
        return $false
    }
}

# Function to force remove directories
function Remove-DirectoryForce {
    param($path)
    if (Test-Path $path) {
        Write-Host "Removing: $path" -ForegroundColor Yellow
        try {
            # First try normal removal
            Remove-Item -Path $path -Recurse -Force -ErrorAction Stop
        }
        catch {
            # If failed, try with takeown and icacls
            Write-Host "   Using elevated permissions..." -ForegroundColor Yellow
            cmd /c "takeown /f `"$path`" /r /d y > nul 2>&1"
            cmd /c "icacls `"$path`" /grant administrators:F /t > nul 2>&1"
            Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

# Kill any running Flutter/Dart processes
Write-Host "Stopping Flutter/Dart processes..."
Get-Process | Where-Object {$_.ProcessName -like "*flutter*" -or $_.ProcessName -like "*dart*" -or $_.ProcessName -like "*chrome*" -and $_.MainWindowTitle -like "*Flutter*"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Check/Enable Developer Mode if requested
if ($EnableDeveloperMode) {
    Enable-DeveloperMode
}

# Clean standard directories
Write-Host "Cleaning build artifacts..."
$dirsToClean = @("build", ".dart_tool", ".flutter-plugins", ".flutter-plugins-dependencies")

foreach ($dir in $dirsToClean) {
    Remove-DirectoryForce $dir
}

# Deep clean if requested
if ($Deep) {
    Write-Host "Deep clean mode..." -ForegroundColor Red
    $deepDirs = @(
        "windows\flutter\ephemeral",
        "linux\flutter\ephemeral", 
        "macos\Flutter\ephemeral",
        "android\.gradle",
        "android\app\build",
        "ios\Pods",
        "ios\.symlinks"
    )
    
    foreach ($dir in $deepDirs) {
        Remove-DirectoryForce $dir
    }
}

# Flutter clean
Write-Host "Running flutter clean..."
flutter clean

# Get dependencies
Write-Host "Getting dependencies..."
flutter pub get

# Run if requested
if ($Run) {
    Write-Host "Starting Flutter app..."
    flutter run -d edge
}

Write-Host ""
Write-Host "Clean complete!" -ForegroundColor Green
Write-Host "Usage: .\flutter-clean.ps1 [-Deep] [-Run] [-EnableDeveloperMode]" -ForegroundColor Cyan
Write-Host "  -Deep: Performs deep clean including platform-specific directories" -ForegroundColor Gray
Write-Host "  -Run: Runs the app after cleaning" -ForegroundColor Gray
Write-Host "  -EnableDeveloperMode: Attempts to enable Windows Developer Mode for symlink support" -ForegroundColor Gray
