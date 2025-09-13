# Audio-Only Drama — Automated FX Engine

A comprehensive Python monorepo with FastAPI backend, Celery worker, Redis, Postgres, and a minimal React/Vite web UI, all Dockerized with docker-compose for dev and prod, including Makefile targets and GitHub Actions CI.

## 🎭 Overview

This project provides a complete development setup for creating automated audio processing pipelines that can:

- Process voice recordings with noise reduction and enhancement
- Apply automated sound effects and background music mixing
- Integrate with WhisperX for speech processing
- Provide a modern web interface for managing projects and processing jobs
- Scale processing with Celery task queues and Redis caching
- Deploy seamlessly with Docker and CI/CD pipelines

## 🚀 Quick Start

### Prerequisites

Before setting up the development environment, ensure you have:

- **Git** - Version control
- **Python 3.11+** - Backend development
- **Node.js LTS** - Frontend development
- **Docker Desktop** - Containerization
- **FFmpeg** - Audio processing
- **Make** - Build automation

### Quick Setup with Docker (Recommended)

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd audio-drama-fx-engine
   ```

2. **Copy environment files:**

   ```bash
   cp env.example .env
   cp web/env.example web/.env
   ```

3. **Start development environment:**

   ```bash
   make dev
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development Setup

1. **Set up Python environment:**

   ```bash
   make setup-python
   ```

2. **Set up Node.js environment:**

   ```bash
   make setup-node
   ```

3. **Start Docker services:**

   ```bash
   make docker-up
   ```

4. **Start development servers locally:**
   ```bash
   make dev-local
   ```

## 📁 Project Structure

```
audio-drama-fx-engine/
├── backend/                    # FastAPI backend application
│   ├── api/                    # API routes and dependencies
│   │   ├── v1/                 # API version 1
│   │   │   ├── endpoints/      # API endpoints
│   │   │   └── api.py          # API router
│   │   └── dependencies.py     # API dependencies
│   ├── tasks/                  # Celery tasks
│   │   ├── audio_processing.py # Audio processing tasks
│   │   ├── whisperx_tasks.py   # WhisperX integration
│   │   └── effects_tasks.py    # Audio effects tasks
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Backend tests
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database configuration
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   └── celery_app.py           # Celery configuration
├── web/                        # React + TypeScript frontend
│   ├── src/                    # Source code
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── hooks/              # Custom React hooks
│   │   ├── lib/                # Utility libraries
│   │   └── test/               # Frontend tests
│   ├── Dockerfile              # Production frontend image
│   ├── Dockerfile.dev          # Development frontend image
│   ├── nginx.conf              # Nginx configuration
│   └── package.json            # Node.js dependencies
├── .github/                    # GitHub Actions CI/CD
│   └── workflows/              # CI/CD workflows
│       ├── ci.yml              # Main CI pipeline
│       └── release.yml         # Release workflow
├── scripts/                    # Setup and utility scripts
│   ├── bootstrap.sh            # macOS/Linux bootstrap
│   ├── bootstrap.ps1           # Windows bootstrap
│   ├── setup-python.sh         # Python environment setup
│   └── init-db.sql             # Database initialization
├── docker-compose.yml          # Base Docker services
├── docker-compose.dev.yml      # Development environment
├── docker-compose.prod.yml     # Production environment
├── Dockerfile                  # Backend production image
├── Dockerfile.celery           # Celery worker image
├── nginx.conf                  # Production nginx config
├── requirements.txt            # Python dependencies
├── Makefile                    # Development tasks
├── env.example                 # Environment variables template
└── README.md                   # This file
```

## 🛠️ Development Commands

### Environment Management

```bash
# Install all dependencies
make install

# Setup Python environment only
make setup-python

# Setup Node.js environment only
make setup-node

# Validate environment
make validate
```

### Docker Services

```bash
# Start development environment (recommended)
make dev

# Start services only (PostgreSQL, Redis)
make docker-up

# Stop services
make docker-down

# View logs
make docker-logs

# Restart services
make docker-restart
```

### Development Servers

```bash
# Start all development servers with Docker
make dev

# Start all development servers locally
make dev-local

# Start backend only
make dev-backend

# Start frontend only
make dev-frontend

# Start Celery worker
make dev-celery
```

### Production

```bash
# Start production environment
make prod

# Build and start production environment
make prod-build

# Build Docker images
make build-docker

# Deploy to Render (placeholder)
make render
```

### Code Quality

```bash
# Run all linting
make lint

# Format all code
make format

# Run tests
make test

# Run tests in Docker
make test-docker

# Run security checks
make security-check
```

### Database Operations

```bash
# Run migrations
make db-migrate

# Reset database (WARNING: deletes all data)
make db-reset
```

### Cleanup

```bash
# Clean all generated files
make clean

# Clean Python files only
make clean-python

# Clean Node.js files only
make clean-node
```

## 🔧 Configuration

### Environment Variables

Copy the environment templates and configure your settings:

```bash
cp env.example .env
cp web/env.example web/.env
```

Key configuration areas:

- **API Keys**: ElevenLabs, OpenAI
- **Database**: PostgreSQL connection settings
- **Redis**: Caching and task queue settings
- **Audio Processing**: File size limits, supported formats
- **Security**: JWT settings, rate limiting
- **Docker**: Container configuration

### Docker Services

The development environment includes:

- **PostgreSQL 16**: Main database
- **Redis 7**: Caching and task queue
- **FastAPI Backend**: Python API server
- **Celery Worker**: Background task processing
- **Celery Beat**: Task scheduler
- **React Frontend**: Web interface
- **Redis Commander**: Redis management UI (optional)
- **pgAdmin**: PostgreSQL management UI (optional)

Access the services:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis Commander: http://localhost:8081
- pgAdmin: http://localhost:8080

## 🎵 Audio Processing Features

### Supported Formats

- **Input**: WAV, MP3, FLAC, M4A, AAC, OGG
- **Output**: WAV, MP3, FLAC, M4A

### Processing Capabilities

- **Voice Enhancement**: Noise reduction, clarity improvement
- **Background Music Mixing**: Automatic level balancing
- **Sound Effects**: Ambient sound addition
- **Compression**: Audio level normalization
- **EQ Adjustment**: Frequency response tuning

### WhisperX Integration

- Speech-to-text transcription
- Speaker diarization
- Language detection
- Word-level timestamps

## 🌐 API Endpoints

### Core Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/status` - API status

### Audio Processing

- `POST /api/audio/upload` - Upload audio files
- `POST /api/audio/process` - Process audio with effects
- `GET /api/audio/jobs` - Get processing jobs

### Effects Management

- `GET /api/effects` - List available effects
- `POST /api/effects` - Create custom effects
- `PUT /api/effects/{id}` - Update effect settings

### Project Management

- `GET /api/projects` - List projects
- `POST /api/projects` - Create new project
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project
- `DELETE /api/projects/{id}` - Delete project

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run Python tests only
make test-python

# Run Node.js tests only
make test-node

# Run with coverage
make test-coverage
```

### Test Structure

- **Backend Tests**: `backend/tests/`
- **Frontend Tests**: `web/src/__tests__/`
- **Integration Tests**: `tests/integration/`
- **E2E Tests**: `tests/e2e/`

## 📊 Monitoring and Logging

### Logs

- **Application Logs**: `logs/app.log`
- **Docker Logs**: `make docker-logs`
- **Development Logs**: Console output

### Health Checks

- **API Health**: `GET /health`
- **Database Health**: Automatic connection checks
- **Redis Health**: Connection monitoring
- **Processing Queue**: Job status monitoring

## 🚀 Deployment

### Development

```bash
# Start development environment with Docker
make dev

# Or start locally
make dev-local
```

### Production

```bash
# Start production environment
make prod

# Build and start production environment
make prod-build
```

### Docker Deployment

```bash
# Build all Docker images
make build-docker

# Run production environment
docker compose -f docker-compose.prod.yml up -d
```

### Render Deployment

```bash
# Deploy to Render (configure manually)
make render
```

The `make render` command provides instructions for deploying to Render.com.

## 🤝 Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Run tests**: `make test`
5. **Format code**: `make format`
6. **Commit changes**: `git commit -m 'Add amazing feature'`
7. **Push to branch**: `git push origin feature/amazing-feature`
8. **Open a Pull Request**

### Code Standards

- **Python**: Black formatting, Flake8 linting, MyPy type checking
- **TypeScript**: ESLint, Prettier formatting
- **Commits**: Conventional commit messages
- **Documentation**: Update README and docstrings
- **CI/CD**: GitHub Actions for automated testing and deployment

### CI/CD Pipeline

The project includes GitHub Actions workflows for:

- **Linting and Formatting**: Automated code quality checks
- **Testing**: Backend and frontend test execution
- **Security Scanning**: Automated security vulnerability checks
- **Docker Building**: Container image building and testing
- **Deployment**: Automated deployment to staging and production

## 📚 Documentation

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **React Documentation**: https://reactjs.org/docs/
- **WhisperX Documentation**: https://github.com/m-bain/whisperX
- **Docker Documentation**: https://docs.docker.com/

## 🐛 Troubleshooting

### Common Issues

1. **Docker services not starting**:

   ```bash
   make docker-down
   make docker-up
   ```

2. **Python dependencies not installing**:

   ```bash
   make clean-python
   make setup-python
   ```

3. **Node.js dependencies issues**:

   ```bash
   make clean-node
   make setup-node
   ```

4. **Port conflicts**:
   - Backend: Change `PORT` in `.env`
   - Frontend: Change port in `web/vite.config.ts`
   - Database: Change ports in `docker-compose.yml`

### Getting Help

- **Check logs**: `make docker-logs`
- **Verify environment**: `make validate`
- **Run diagnostics**: `python verify.py`

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **FastAPI** - Modern, fast web framework for building APIs
- **React** - A JavaScript library for building user interfaces
- **WhisperX** - Advanced speech recognition and processing
- **FFmpeg** - Complete, cross-platform solution for audio/video processing
- **Docker** - Containerization platform for consistent development environments

---

**Happy coding! 🎭🎵**
