#!/usr/bin/env python3
"""
Audio-Only Drama — Automated FX Engine
Verification script to test all dependencies and environment setup
"""

import sys
import subprocess
import importlib
import os
from pathlib import Path
from typing import List, Tuple, Optional

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str) -> None:
    """Print a formatted header"""
    print(f"\n{Colors.CYAN}{Colors.BOLD}{title}{Colors.END}")
    print("=" * len(title))

def print_success(message: str) -> None:
    """Print a success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str) -> None:
    """Print an error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str) -> None:
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str) -> None:
    """Print an info message"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def run_command(command: List[str], capture_output: bool = True) -> Tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr"""
    try:
        result = subprocess.run(
            command,
            capture_output=capture_output,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except FileNotFoundError:
        return False, "", f"Command not found: {command[0]}"
    except Exception as e:
        return False, "", str(e)

def check_python_version() -> bool:
    """Check if Python version is 3.11+"""
    print_header("Python Version Check")
    
    version = sys.version_info
    print_info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor} is supported")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} is not supported. Need Python 3.11+")
        return False

def check_python_packages() -> bool:
    """Check if required Python packages are installed"""
    print_header("Python Package Check")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'alembic',
        'psycopg2',
        'celery',
        'redis',
        'requests',
        'soundfile',
        'librosa',
        'ffmpeg',
        'pydub',
        'httpx',
        'tqdm'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            # Handle special cases for package names
            import_name = package
            if package == 'psycopg2':
                import_name = 'psycopg2'
            elif package == 'ffmpeg':
                import_name = 'ffmpeg'
            
            importlib.import_module(import_name)
            print_success(f"{package} is installed")
        except ImportError:
            print_error(f"{package} is not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print_warning(f"Missing packages: {', '.join(missing_packages)}")
        return False
    
    return True

def check_torch_installation() -> bool:
    """Check PyTorch installation and GPU availability"""
    print_header("PyTorch Check")
    
    try:
        import torch
        print_success(f"PyTorch version: {torch.__version__}")
        
        # Check CUDA availability
        if torch.cuda.is_available():
            print_success(f"CUDA is available with {torch.cuda.device_count()} GPU(s)")
            for i in range(torch.cuda.device_count()):
                gpu_name = torch.cuda.get_device_name(i)
                print_info(f"GPU {i}: {gpu_name}")
        else:
            print_info("CUDA is not available (CPU-only mode)")
        
        return True
    except ImportError:
        print_error("PyTorch is not installed")
        return False

def check_whisperx() -> bool:
    """Check WhisperX installation"""
    print_header("WhisperX Check")
    
    try:
        import whisperx
        print_success(f"WhisperX is installed")
        
        # Try to get version if available
        try:
            version = whisperx.__version__
            print_info(f"WhisperX version: {version}")
        except AttributeError:
            print_info("WhisperX version not available")
        
        return True
    except ImportError:
        print_error("WhisperX is not installed")
        return False

def check_ffmpeg() -> bool:
    """Check FFmpeg installation"""
    print_header("FFmpeg Check")
    
    success, stdout, stderr = run_command(['ffmpeg', '-version'])
    
    if success:
        # Extract version from first line
        first_line = stdout.split('\n')[0] if stdout else "Unknown version"
        print_success(f"FFmpeg is installed: {first_line}")
        return True
    else:
        print_error(f"FFmpeg is not available: {stderr}")
        return False

def check_docker_services() -> bool:
    """Check if Docker services are running"""
    print_header("Docker Services Check")
    
    # Check if Docker is running
    success, stdout, stderr = run_command(['docker', 'ps'])
    if not success:
        print_error(f"Docker is not running: {stderr}")
        return False
    
    print_success("Docker is running")
    
    # Check specific services
    services = ['postgres', 'redis']
    all_services_running = True
    
    for service in services:
        success, stdout, stderr = run_command(['docker', 'compose', 'ps', service])
        if success and service in stdout:
            print_success(f"{service} service is running")
        else:
            print_error(f"{service} service is not running")
            all_services_running = False
    
    return all_services_running

def check_node_environment() -> bool:
    """Check Node.js environment"""
    print_header("Node.js Environment Check")
    
    # Check Node.js version
    success, stdout, stderr = run_command(['node', '--version'])
    if success:
        print_success(f"Node.js version: {stdout.strip()}")
    else:
        print_error(f"Node.js is not installed: {stderr}")
        return False
    
    # Check npm version
    success, stdout, stderr = run_command(['npm', '--version'])
    if success:
        print_success(f"npm version: {stdout.strip()}")
    else:
        print_error(f"npm is not installed: {stderr}")
        return False
    
    # Check if web directory exists and has node_modules
    web_dir = Path('web')
    if web_dir.exists():
        node_modules = web_dir / 'node_modules'
        if node_modules.exists():
            print_success("Node.js dependencies are installed")
            return True
        else:
            print_warning("Node.js dependencies are not installed")
            return False
    else:
        print_warning("Web directory not found")
        return False

def check_environment_files() -> bool:
    """Check if required environment files exist"""
    print_header("Environment Files Check")
    
    required_files = [
        '.env.example',
        '.gitignore',
        'requirements.txt',
        'docker-compose.yml'
    ]
    
    all_files_exist = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            print_success(f"{file_path} exists")
        else:
            print_error(f"{file_path} is missing")
            all_files_exist = False
    
    # Check if .env exists (optional)
    if Path('.env').exists():
        print_success(".env file exists")
    else:
        print_warning(".env file not found (copy from .env.example)")
    
    return all_files_exist

def check_virtual_environment() -> bool:
    """Check if virtual environment is properly set up"""
    print_header("Virtual Environment Check")
    
    venv_path = Path('.venv')
    if not venv_path.exists():
        print_error("Virtual environment (.venv) not found")
        return False
    
    print_success("Virtual environment exists")
    
    # Check if we're in the virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Running in virtual environment")
    else:
        print_warning("Not running in virtual environment")
    
    return True

def run_quick_tests() -> bool:
    """Run quick functionality tests"""
    print_header("Quick Functionality Tests")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Import FastAPI
    total_tests += 1
    try:
        import fastapi
        print_success("FastAPI import test passed")
        tests_passed += 1
    except ImportError:
        print_error("FastAPI import test failed")
    
    # Test 2: Import SQLAlchemy
    total_tests += 1
    try:
        import sqlalchemy
        print_success("SQLAlchemy import test passed")
        tests_passed += 1
    except ImportError:
        print_error("SQLAlchemy import test failed")
    
    # Test 3: Test Redis connection (if available)
    total_tests += 1
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print_success("Redis connection test passed")
        tests_passed += 1
    except Exception as e:
        print_warning(f"Redis connection test failed: {e}")
    
    # Test 4: Test audio file processing
    total_tests += 1
    try:
        import soundfile
        import librosa
        print_success("Audio processing libraries test passed")
        tests_passed += 1
    except ImportError:
        print_error("Audio processing libraries test failed")
    
    print_info(f"Tests passed: {tests_passed}/{total_tests}")
    return tests_passed == total_tests

def main():
    """Main verification function"""
    print(f"{Colors.CYAN}{Colors.BOLD}")
    print("🎭 Audio-Only Drama — Automated FX Engine")
    print("Environment Verification Script")
    print("=" * 50)
    print(f"{Colors.END}")
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Python Packages", check_python_packages),
        ("PyTorch Installation", check_torch_installation),
        ("WhisperX Installation", check_whisperx),
        ("FFmpeg Installation", check_ffmpeg),
        ("Docker Services", check_docker_services),
        ("Node.js Environment", check_node_environment),
        ("Environment Files", check_environment_files),
        ("Quick Tests", run_quick_tests),
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_func in checks:
        try:
            if check_func():
                passed_checks += 1
        except Exception as e:
            print_error(f"{check_name} check failed with error: {e}")
    
    # Summary
    print_header("Verification Summary")
    
    if passed_checks == total_checks:
        print_success(f"All {total_checks} checks passed! 🎉")
        print_info("Your development environment is ready!")
        print_info("Next steps:")
        print_info("1. Copy .env.example to .env and configure your settings")
        print_info("2. Run 'make dev' to start the development servers")
        print_info("3. Visit http://localhost:3000 for the web interface")
        print_info("4. Visit http://localhost:8000/docs for the API documentation")
        return 0
    else:
        failed_checks = total_checks - passed_checks
        print_error(f"{failed_checks} out of {total_checks} checks failed")
        print_warning("Please fix the issues above before proceeding")
        print_info("Run 'make setup-python' to install Python dependencies")
        print_info("Run 'make setup-node' to install Node.js dependencies")
        print_info("Run 'make docker-up' to start Docker services")
        return 1

if __name__ == "__main__":
    sys.exit(main())
