# Audio-Only Drama — Automated FX Engine
# Bootstrap script for Windows
# This script installs prerequisites or verifies they're present

param(
    [switch]$Force
)

Write-Host "🎭 Audio-Only Drama — Automated FX Engine Bootstrap" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Function to check if a command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to install using winget
function Install-WithWinget {
    param($Package, $Name)
    if (Test-Command "winget") {
        Write-Host "Installing $Name using winget..." -ForegroundColor Yellow
        winget install $Package --accept-package-agreements --accept-source-agreements
        return $true
    }
    return $false
}

# Function to install using chocolatey
function Install-WithChoco {
    param($Package, $Name)
    if (Test-Command "choco") {
        Write-Host "Installing $Name using chocolatey..." -ForegroundColor Yellow
        choco install $Package -y
        return $true
    }
    return $false
}

$installed = @()
$failed = @()

# Check Git
Write-Host "`n📋 Checking Git..." -ForegroundColor Green
if (Test-Command "git") {
    $version = git --version
    Write-Host "✅ Git found: $version" -ForegroundColor Green
    $installed += "Git"
} else {
    Write-Host "❌ Git not found. Installing..." -ForegroundColor Red
    if (-not (Install-WithWinget "Git.Git" "Git") -and -not (Install-WithChoco "git" "Git")) {
        Write-Host "⚠️  Manual installation required for Git:" -ForegroundColor Yellow
        Write-Host "   Download from: https://git-scm.com/download/win" -ForegroundColor White
        $failed += "Git"
    } else {
        $installed += "Git"
    }
}

# Check Python 3.11+
Write-Host "`n🐍 Checking Python 3.11+..." -ForegroundColor Green
if (Test-Command "python") {
    $version = python --version 2>&1
    if ($version -match "Python 3\.(1[1-9]|[2-9][0-9])") {
        Write-Host "✅ Python found: $version" -ForegroundColor Green
        $installed += "Python"
    } else {
        Write-Host "❌ Python version too old: $version (need 3.11+)" -ForegroundColor Red
        if (-not (Install-WithWinget "Python.Python.3.11" "Python 3.11") -and -not (Install-WithChoco "python311" "Python 3.11")) {
            Write-Host "⚠️  Manual installation required for Python 3.11+:" -ForegroundColor Yellow
            Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor White
            $failed += "Python"
        } else {
            $installed += "Python"
        }
    }
} else {
    Write-Host "❌ Python not found. Installing..." -ForegroundColor Red
    if (-not (Install-WithWinget "Python.Python.3.11" "Python 3.11") -and -not (Install-WithChoco "python311" "Python 3.11")) {
        Write-Host "⚠️  Manual installation required for Python 3.11+:" -ForegroundColor Yellow
        Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor White
        $failed += "Python"
    } else {
        $installed += "Python"
    }
}

# Check Node.js LTS
Write-Host "`n📦 Checking Node.js LTS..." -ForegroundColor Green
if (Test-Command "node") {
    $version = node --version
    Write-Host "✅ Node.js found: $version" -ForegroundColor Green
    $installed += "Node.js"
} else {
    Write-Host "❌ Node.js not found. Installing..." -ForegroundColor Red
    if (-not (Install-WithWinget "OpenJS.NodeJS.LTS" "Node.js LTS") -and -not (Install-WithChoco "nodejs-lts" "Node.js LTS")) {
        Write-Host "⚠️  Manual installation required for Node.js LTS:" -ForegroundColor Yellow
        Write-Host "   Download from: https://nodejs.org/" -ForegroundColor White
        $failed += "Node.js"
    } else {
        $installed += "Node.js"
    }
}

# Check Docker Desktop
Write-Host "`n🐳 Checking Docker Desktop..." -ForegroundColor Green
if (Test-Command "docker") {
    $version = docker --version
    Write-Host "✅ Docker found: $version" -ForegroundColor Green
    $installed += "Docker"
} else {
    Write-Host "❌ Docker not found. Installing..." -ForegroundColor Red
    if (-not (Install-WithWinget "Docker.DockerDesktop" "Docker Desktop") -and -not (Install-WithChoco "docker-desktop" "Docker Desktop")) {
        Write-Host "⚠️  Manual installation required for Docker Desktop:" -ForegroundColor Yellow
        Write-Host "   Download from: https://www.docker.com/products/docker-desktop/" -ForegroundColor White
        Write-Host "   Note: Requires Windows 10/11 Pro, Enterprise, or Education" -ForegroundColor White
        $failed += "Docker"
    } else {
        $installed += "Docker"
    }
}

# Check FFmpeg
Write-Host "`n🎵 Checking FFmpeg..." -ForegroundColor Green
if (Test-Command "ffmpeg") {
    $version = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "✅ FFmpeg found: $version" -ForegroundColor Green
    $installed += "FFmpeg"
} else {
    Write-Host "❌ FFmpeg not found. Installing..." -ForegroundColor Red
    if (-not (Install-WithWinget "Gyan.FFmpeg" "FFmpeg") -and -not (Install-WithChoco "ffmpeg" "FFmpeg")) {
        Write-Host "⚠️  Manual installation required for FFmpeg:" -ForegroundColor Yellow
        Write-Host "   Download from: https://ffmpeg.org/download.html" -ForegroundColor White
        Write-Host "   Or use: winget install Gyan.FFmpeg" -ForegroundColor White
        $failed += "FFmpeg"
    } else {
        $installed += "FFmpeg"
    }
}

# Summary
Write-Host "`n📊 Installation Summary" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

if ($installed.Count -gt 0) {
    Write-Host "✅ Successfully installed/verified:" -ForegroundColor Green
    foreach ($item in $installed) {
        Write-Host "   • $item" -ForegroundColor White
    }
}

if ($failed.Count -gt 0) {
    Write-Host "`n❌ Manual installation required:" -ForegroundColor Red
    foreach ($item in $failed) {
        Write-Host "   • $item" -ForegroundColor White
    }
    Write-Host "`n⚠️  Please install the above tools manually and re-run this script." -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "`n🎉 All prerequisites are ready!" -ForegroundColor Green
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Run: make validate" -ForegroundColor White
    Write-Host "2. Or run: docker compose up -d" -ForegroundColor White
    Write-Host "3. Then: make setup-python" -ForegroundColor White
}
