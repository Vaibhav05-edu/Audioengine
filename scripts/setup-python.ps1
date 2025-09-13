# Audio-Only Drama — Automated FX Engine
# Python environment setup script for Windows

param(
    [switch]$Force
)

Write-Host "🐍 Setting up Python environment" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Check if Python 3.11+ is available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "Found Python version: $pythonVersion" -ForegroundColor Blue

# Check if version is 3.11+
$versionCheck = python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python 3.11+ required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Check for NVIDIA GPU
Write-Host "Checking for NVIDIA GPU..." -ForegroundColor Yellow
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "NVIDIA GPU detected. Please confirm your CUDA version:" -ForegroundColor Blue
    nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits
    Write-Host "For CUDA 11.8: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor Yellow
    Write-Host "For CUDA 12.1: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121" -ForegroundColor Yellow
    Write-Host "Please run the appropriate command manually, then continue with: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "Or press Enter to install CPU-only version..." -ForegroundColor Blue
    Read-Host
}

# Install CPU-only PyTorch by default
Write-Host "Installing PyTorch (CPU-only)..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Install WhisperX
Write-Host "Installing WhisperX..." -ForegroundColor Yellow
pip install git+https://github.com/m-bain/whisperx.git

Write-Host "🎉 Python environment setup complete!" -ForegroundColor Green
Write-Host "To activate the environment:" -ForegroundColor Cyan
Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "To deactivate:" -ForegroundColor Cyan
Write-Host "  deactivate" -ForegroundColor White
