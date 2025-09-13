#!/bin/bash
# Audio-Only Drama — Automated FX Engine
# Bootstrap script for macOS/Linux
# This script installs prerequisites or verifies they're present

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

echo -e "${CYAN}🎭 Audio-Only Drama — Automated FX Engine Bootstrap${NC}"
echo -e "${CYAN}=================================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "rhel"
        elif command_exists pacman; then
            echo "arch"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

# Function to install using brew (macOS)
install_with_brew() {
    local package=$1
    local name=$2
    
    if command_exists brew; then
        echo -e "${YELLOW}Installing $name using Homebrew...${NC}"
        brew install "$package"
        return 0
    fi
    return 1
}

# Function to install using apt (Ubuntu/Debian)
install_with_apt() {
    local package=$1
    local name=$2
    
    if command_exists apt-get; then
        echo -e "${YELLOW}Installing $name using apt...${NC}"
        sudo apt-get update
        sudo apt-get install -y "$package"
        return 0
    fi
    return 1
}

# Function to install using yum (RHEL/CentOS)
install_with_yum() {
    local package=$1
    local name=$2
    
    if command_exists yum; then
        echo -e "${YELLOW}Installing $name using yum...${NC}"
        sudo yum install -y "$package"
        return 0
    fi
    return 1
}

# Function to install using pacman (Arch)
install_with_pacman() {
    local package=$1
    local name=$2
    
    if command_exists pacman; then
        echo -e "${YELLOW}Installing $name using pacman...${NC}"
        sudo pacman -S --noconfirm "$package"
        return 0
    fi
    return 1
}

OS=$(detect_os)
installed=()
failed=()

echo -e "\n${BLUE}Detected OS: $OS${NC}"

# Check Git
echo -e "\n${GREEN}📋 Checking Git...${NC}"
if command_exists git; then
    version=$(git --version)
    echo -e "${GREEN}✅ Git found: $version${NC}"
    installed+=("Git")
else
    echo -e "${RED}❌ Git not found. Installing...${NC}"
    case $OS in
        "macos")
            if ! install_with_brew "git" "Git"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Git:${NC}"
                echo -e "${WHITE}   brew install git${NC}"
                failed+=("Git")
            else
                installed+=("Git")
            fi
            ;;
        "ubuntu")
            if ! install_with_apt "git" "Git"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Git:${NC}"
                echo -e "${WHITE}   sudo apt-get install git${NC}"
                failed+=("Git")
            else
                installed+=("Git")
            fi
            ;;
        "rhel")
            if ! install_with_yum "git" "Git"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Git:${NC}"
                echo -e "${WHITE}   sudo yum install git${NC}"
                failed+=("Git")
            else
                installed+=("Git")
            fi
            ;;
        "arch")
            if ! install_with_pacman "git" "Git"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Git:${NC}"
                echo -e "${WHITE}   sudo pacman -S git${NC}"
                failed+=("Git")
            else
                installed+=("Git")
            fi
            ;;
        *)
            echo -e "${YELLOW}⚠️  Manual installation required for Git:${NC}"
            echo -e "${WHITE}   Download from: https://git-scm.com/downloads${NC}"
            failed+=("Git")
            ;;
    esac
fi

# Check Python 3.11+
echo -e "\n${GREEN}🐍 Checking Python 3.11+...${NC}"
if command_exists python3; then
    version=$(python3 --version 2>&1)
    if [[ $version =~ Python\ 3\.(1[1-9]|[2-9][0-9]) ]]; then
        echo -e "${GREEN}✅ Python found: $version${NC}"
        installed+=("Python")
    else
        echo -e "${RED}❌ Python version too old: $version (need 3.11+)${NC}"
        case $OS in
            "macos")
                if ! install_with_brew "python@3.11" "Python 3.11"; then
                    echo -e "${YELLOW}⚠️  Manual installation required for Python 3.11+:${NC}"
                    echo -e "${WHITE}   brew install python@3.11${NC}"
                    failed+=("Python")
                else
                    installed+=("Python")
                fi
                ;;
            "ubuntu")
                if ! install_with_apt "python3.11" "Python 3.11"; then
                    echo -e "${YELLOW}⚠️  Manual installation required for Python 3.11+:${NC}"
                    echo -e "${WHITE}   sudo apt-get install python3.11 python3.11-venv python3.11-pip${NC}"
                    failed+=("Python")
                else
                    installed+=("Python")
                fi
                ;;
            *)
                echo -e "${YELLOW}⚠️  Manual installation required for Python 3.11+:${NC}"
                echo -e "${WHITE}   Download from: https://www.python.org/downloads/${NC}"
                failed+=("Python")
                ;;
        esac
    fi
else
    echo -e "${RED}❌ Python not found. Installing...${NC}"
    case $OS in
        "macos")
            if ! install_with_brew "python@3.11" "Python 3.11"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Python 3.11+:${NC}"
                echo -e "${WHITE}   brew install python@3.11${NC}"
                failed+=("Python")
            else
                installed+=("Python")
            fi
            ;;
        "ubuntu")
            if ! install_with_apt "python3.11 python3.11-venv python3.11-pip" "Python 3.11"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Python 3.11+:${NC}"
                echo -e "${WHITE}   sudo apt-get install python3.11 python3.11-venv python3.11-pip${NC}"
                failed+=("Python")
            else
                installed+=("Python")
            fi
            ;;
        *)
            echo -e "${YELLOW}⚠️  Manual installation required for Python 3.11+:${NC}"
            echo -e "${WHITE}   Download from: https://www.python.org/downloads/${NC}"
            failed+=("Python")
            ;;
    esac
fi

# Check Node.js LTS
echo -e "\n${GREEN}📦 Checking Node.js LTS...${NC}"
if command_exists node; then
    version=$(node --version)
    echo -e "${GREEN}✅ Node.js found: $version${NC}"
    installed+=("Node.js")
else
    echo -e "${RED}❌ Node.js not found. Installing...${NC}"
    case $OS in
        "macos")
            if ! install_with_brew "node" "Node.js LTS"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Node.js LTS:${NC}"
                echo -e "${WHITE}   brew install node${NC}"
                failed+=("Node.js")
            else
                installed+=("Node.js")
            fi
            ;;
        "ubuntu")
            if ! install_with_apt "nodejs npm" "Node.js LTS"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Node.js LTS:${NC}"
                echo -e "${WHITE}   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -${NC}"
                echo -e "${WHITE}   sudo apt-get install -y nodejs${NC}"
                failed+=("Node.js")
            else
                installed+=("Node.js")
            fi
            ;;
        *)
            echo -e "${YELLOW}⚠️  Manual installation required for Node.js LTS:${NC}"
            echo -e "${WHITE}   Download from: https://nodejs.org/${NC}"
            failed+=("Node.js")
            ;;
    esac
fi

# Check Docker
echo -e "\n${GREEN}🐳 Checking Docker...${NC}"
if command_exists docker; then
    version=$(docker --version)
    echo -e "${GREEN}✅ Docker found: $version${NC}"
    installed+=("Docker")
else
    echo -e "${RED}❌ Docker not found. Installing...${NC}"
    case $OS in
        "macos")
            if ! install_with_brew "docker" "Docker Desktop"; then
                echo -e "${YELLOW}⚠️  Manual installation required for Docker Desktop:${NC}"
                echo -e "${WHITE}   Download from: https://www.docker.com/products/docker-desktop/${NC}"
                failed+=("Docker")
            else
                installed+=("Docker")
            fi
            ;;
        "ubuntu")
            echo -e "${YELLOW}⚠️  Manual installation required for Docker:${NC}"
            echo -e "${WHITE}   curl -fsSL https://get.docker.com -o get-docker.sh${NC}"
            echo -e "${WHITE}   sudo sh get-docker.sh${NC}"
            echo -e "${WHITE}   sudo usermod -aG docker \$USER${NC}"
            failed+=("Docker")
            ;;
        *)
            echo -e "${YELLOW}⚠️  Manual installation required for Docker:${NC}"
            echo -e "${WHITE}   Download from: https://www.docker.com/products/docker-desktop/${NC}"
            failed+=("Docker")
            ;;
    esac
fi

# Check FFmpeg
echo -e "\n${GREEN}🎵 Checking FFmpeg...${NC}"
if command_exists ffmpeg; then
    version=$(ffmpeg -version 2>&1 | head -n 1)
    echo -e "${GREEN}✅ FFmpeg found: $version${NC}"
    installed+=("FFmpeg")
else
    echo -e "${RED}❌ FFmpeg not found. Installing...${NC}"
    case $OS in
        "macos")
            if ! install_with_brew "ffmpeg" "FFmpeg"; then
                echo -e "${YELLOW}⚠️  Manual installation required for FFmpeg:${NC}"
                echo -e "${WHITE}   brew install ffmpeg${NC}"
                failed+=("FFmpeg")
            else
                installed+=("FFmpeg")
            fi
            ;;
        "ubuntu")
            if ! install_with_apt "ffmpeg" "FFmpeg"; then
                echo -e "${YELLOW}⚠️  Manual installation required for FFmpeg:${NC}"
                echo -e "${WHITE}   sudo apt-get install ffmpeg${NC}"
                failed+=("FFmpeg")
            else
                installed+=("FFmpeg")
            fi
            ;;
        "rhel")
            if ! install_with_yum "ffmpeg" "FFmpeg"; then
                echo -e "${YELLOW}⚠️  Manual installation required for FFmpeg:${NC}"
                echo -e "${WHITE}   sudo yum install epel-release${NC}"
                echo -e "${WHITE}   sudo yum install ffmpeg${NC}"
                failed+=("FFmpeg")
            else
                installed+=("FFmpeg")
            fi
            ;;
        "arch")
            if ! install_with_pacman "ffmpeg" "FFmpeg"; then
                echo -e "${YELLOW}⚠️  Manual installation required for FFmpeg:${NC}"
                echo -e "${WHITE}   sudo pacman -S ffmpeg${NC}"
                failed+=("FFmpeg")
            else
                installed+=("FFmpeg")
            fi
            ;;
        *)
            echo -e "${YELLOW}⚠️  Manual installation required for FFmpeg:${NC}"
            echo -e "${WHITE}   Download from: https://ffmpeg.org/download.html${NC}"
            failed+=("FFmpeg")
            ;;
    esac
fi

# Summary
echo -e "\n${CYAN}📊 Installation Summary${NC}"
echo -e "${CYAN}=====================${NC}"

if [ ${#installed[@]} -gt 0 ]; then
    echo -e "${GREEN}✅ Successfully installed/verified:${NC}"
    for item in "${installed[@]}"; do
        echo -e "${WHITE}   • $item${NC}"
    done
fi

if [ ${#failed[@]} -gt 0 ]; then
    echo -e "\n${RED}❌ Manual installation required:${NC}"
    for item in "${failed[@]}"; do
        echo -e "${WHITE}   • $item${NC}"
    done
    echo -e "\n${YELLOW}⚠️  Please install the above tools manually and re-run this script.${NC}"
    exit 1
else
    echo -e "\n${GREEN}🎉 All prerequisites are ready!${NC}"
    echo -e "${CYAN}Next steps:${NC}"
    echo -e "${WHITE}1. Run: make validate${NC}"
    echo -e "${WHITE}2. Or run: docker compose up -d${NC}"
    echo -e "${WHITE}3. Then: make setup-python${NC}"
fi
