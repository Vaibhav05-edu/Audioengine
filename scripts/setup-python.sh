#!/bin/bash
# Audio-Only Drama — Automated FX Engine
# Python environment setup script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}🐍 Setting up Python environment${NC}"
echo -e "${CYAN}===============================${NC}"

# Check if Python 3.11+ is available
PYTHON_CMD=""
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v /opt/homebrew/bin/python3.11 &> /dev/null; then
    PYTHON_CMD="/opt/homebrew/bin/python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+ first.${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo -e "${BLUE}Found Python version: $PYTHON_VERSION${NC}"

# Check if version is 3.11+
if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
    echo -e "${RED}❌ Python 3.11+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install PyTorch based on GPU availability
echo -e "${YELLOW}Checking for NVIDIA GPU...${NC}"
if command -v nvidia-smi &> /dev/null; then
    echo -e "${BLUE}NVIDIA GPU detected. Please confirm your CUDA version:${NC}"
    nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits
    echo -e "${YELLOW}For CUDA 11.8: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118${NC}"
    echo -e "${YELLOW}For CUDA 12.1: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121${NC}"
    echo -e "${YELLOW}Please run the appropriate command manually, then continue with: pip install -r requirements.txt${NC}"
    echo -e "${BLUE}Or press Enter to install CPU-only version...${NC}"
    read -r
fi

# Install CPU-only PyTorch by default
echo -e "${YELLOW}Installing PyTorch (CPU-only)...${NC}"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install other requirements
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Install WhisperX
echo -e "${YELLOW}Installing WhisperX...${NC}"
pip install git+https://github.com/m-bain/whisperx.git

echo -e "${GREEN}🎉 Python environment setup complete!${NC}"
echo -e "${CYAN}To activate the environment:${NC}"
echo -e "${WHITE}  source .venv/bin/activate${NC}"
echo -e "${CYAN}To deactivate:${NC}"
echo -e "${WHITE}  deactivate${NC}"
