# Audio-Only Drama — Automated FX Engine
# Makefile for development tasks

.PHONY: help install validate setup-python setup-node docker-up docker-down docker-logs clean test lint format

# Default target
help: ## Show this help message
	@echo "Audio-Only Drama — Automated FX Engine"
	@echo "======================================"
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# =============================================================================
# INSTALLATION AND SETUP
# =============================================================================

install: ## Install all dependencies and setup environment
	@echo "🚀 Setting up Audio Drama FX Engine..."
	@$(MAKE) setup-python
	@$(MAKE) setup-node
	@$(MAKE) docker-up
	@echo "✅ Installation complete!"

setup-python: ## Setup Python virtual environment and install dependencies
	@echo "🐍 Setting up Python environment..."
	@if [ -f "scripts/setup-python.sh" ]; then \
		chmod +x scripts/setup-python.sh && ./scripts/setup-python.sh; \
	else \
		echo "❌ Python setup script not found"; \
		exit 1; \
	fi

setup-node: ## Setup Node.js dependencies
	@echo "📦 Setting up Node.js environment..."
	@cd web && npm install
	@echo "✅ Node.js setup complete!"

# =============================================================================
# DOCKER SERVICES
# =============================================================================

docker-up: ## Start Docker services (PostgreSQL and Redis)
	@echo "🐳 Starting Docker services..."
	@docker compose up -d
	@echo "⏳ Waiting for services to be ready..."
	@sleep 10
	@$(MAKE) docker-health-check
	@echo "✅ Docker services are running!"

docker-down: ## Stop Docker services
	@echo "🛑 Stopping Docker services..."
	@docker compose down
	@echo "✅ Docker services stopped!"

docker-logs: ## Show Docker services logs
	@docker compose logs -f

docker-restart: ## Restart Docker services
	@$(MAKE) docker-down
	@$(MAKE) docker-up

docker-health-check: ## Check health of Docker services
	@echo "🔍 Checking service health..."
	@docker compose ps
	@echo "✅ Health check complete!"

# =============================================================================
# VALIDATION AND TESTING
# =============================================================================

validate: ## Validate the entire development environment
	@echo "🔍 Validating development environment..."
	@$(MAKE) check-prerequisites
	@$(MAKE) docker-health-check
	@$(MAKE) python-verify
	@echo "✅ Environment validation complete!"

check-prerequisites: ## Check if all prerequisites are installed
	@echo "📋 Checking prerequisites..."
	@command -v git >/dev/null 2>&1 || { echo "❌ Git not found"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 not found"; exit 1; }
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js not found"; exit 1; }
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found"; exit 1; }
	@command -v ffmpeg >/dev/null 2>&1 || { echo "❌ FFmpeg not found"; exit 1; }
	@echo "✅ All prerequisites found!"

python-verify: ## Verify Python environment and dependencies
	@echo "🐍 Verifying Python environment..."
	@if [ -f ".venv/bin/python" ]; then \
		.venv/bin/python verify.py; \
	else \
		echo "❌ Python virtual environment not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

test: ## Run all tests
	@echo "🧪 Running tests..."
	@$(MAKE) test-python
	@$(MAKE) test-node

test-python: ## Run Python tests only
	@echo "🐍 Running Python tests..."
	@if [ -f ".venv/bin/python" ]; then \
		.venv/bin/python -m pytest backend/tests/ -v --cov=backend --cov-report=html --cov-report=term; \
	else \
		echo "❌ Python virtual environment not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

test-node: ## Run Node.js tests only
	@echo "📦 Running Node.js tests..."
	@cd web && npm test

test-docker: ## Run tests in Docker
	@echo "🧪 Running tests in Docker..."
	@docker compose -f docker-compose.dev.yml run --rm backend pytest -v
	@docker compose -f docker-compose.dev.yml run --rm frontend npm test

# =============================================================================
# CODE QUALITY
# =============================================================================

lint: ## Run linting on all code
	@echo "🔍 Running linting..."
	@$(MAKE) lint-python
	@$(MAKE) lint-node

lint-python: ## Run Python linting
	@echo "🐍 Running Python linting..."
	@if [ -f ".venv/bin/flake8" ]; then \
		.venv/bin/flake8 . --exclude=.venv,node_modules,web; \
	else \
		echo "❌ Flake8 not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

lint-node: ## Run Node.js linting
	@echo "📦 Running Node.js linting..."
	@cd web && npm run lint

format: ## Format all code
	@echo "🎨 Formatting code..."
	@$(MAKE) format-python
	@$(MAKE) format-node

format-python: ## Format Python code
	@echo "🐍 Formatting Python code..."
	@if [ -f ".venv/bin/black" ]; then \
		.venv/bin/black . --exclude=".venv|node_modules|web"; \
		.venv/bin/isort . --skip-glob=".venv/*" --skip-glob="web/*"; \
	else \
		echo "❌ Black/isort not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

format-node: ## Format Node.js code
	@echo "📦 Formatting Node.js code..."
	@cd web && npm run lint:fix

# =============================================================================
# DEVELOPMENT SERVERS
# =============================================================================

dev: ## Start all development servers using Docker Compose
	@echo "🚀 Starting development environment..."
	@docker compose -f docker-compose.dev.yml up --build

dev-local: ## Start all development servers locally (without Docker)
	@echo "🚀 Starting development servers locally..."
	@$(MAKE) dev-backend &
	@$(MAKE) dev-frontend &
	@wait

dev-backend: ## Start Python backend server locally
	@echo "🐍 Starting Python backend server..."
	@if [ -f ".venv/bin/uvicorn" ]; then \
		.venv/bin/uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "❌ Uvicorn not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

dev-frontend: ## Start Node.js frontend server locally
	@echo "📦 Starting Node.js frontend server..."
	@cd web && npm run dev

dev-celery: ## Start Celery worker locally
	@echo "🔄 Starting Celery worker..."
	@if [ -f ".venv/bin/celery" ]; then \
		.venv/bin/celery -A backend.celery_app worker --loglevel=info; \
	else \
		echo "❌ Celery not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

# =============================================================================
# BUILD AND DEPLOYMENT
# =============================================================================

build: ## Build all components
	@echo "🔨 Building all components..."
	@$(MAKE) build-python
	@$(MAKE) build-node

build-python: ## Build Python components
	@echo "🐍 Building Python components..."
	@if [ -f ".venv/bin/python" ]; then \
		.venv/bin/python -m pip install -e .; \
	else \
		echo "❌ Python virtual environment not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

build-node: ## Build Node.js frontend
	@echo "📦 Building Node.js frontend..."
	@cd web && npm run build

build-docker: ## Build Docker images
	@echo "🐳 Building Docker images..."
	@docker build -t audio-drama-fx-backend .
	@docker build -t audio-drama-fx-celery -f Dockerfile.celery .
	@docker build -t audio-drama-fx-frontend ./web

prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	@docker compose -f docker-compose.prod.yml up -d

prod-build: ## Build and start production environment
	@echo "🚀 Building and starting production environment..."
	@docker compose -f docker-compose.prod.yml up --build -d

render: ## Deploy to Render (placeholder)
	@echo "🚀 Deploying to Render..."
	@echo "⚠️  This is a placeholder. Configure your Render deployment manually."
	@echo "📋 Steps to deploy to Render:"
	@echo "   1. Create a new Web Service on Render"
	@echo "   2. Connect your GitHub repository"
	@echo "   3. Set build command: make build-docker"
	@echo "   4. Set start command: uvicorn backend.main:app --host 0.0.0.0 --port 8000"
	@echo "   5. Add environment variables from .env.example"

# =============================================================================
# CLEANUP
# =============================================================================

clean: ## Clean all generated files and caches
	@echo "🧹 Cleaning up..."
	@$(MAKE) clean-python
	@$(MAKE) clean-node
	@$(MAKE) clean-docker
	@echo "✅ Cleanup complete!"

clean-python: ## Clean Python cache and temporary files
	@echo "🐍 Cleaning Python files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true

clean-node: ## Clean Node.js cache and temporary files
	@echo "📦 Cleaning Node.js files..."
	@cd web && rm -rf node_modules dist .cache 2>/dev/null || true

clean-docker: ## Clean Docker containers and volumes
	@echo "🐳 Cleaning Docker files..."
	@docker compose down -v 2>/dev/null || true
	@docker system prune -f 2>/dev/null || true

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

db-migrate: ## Run database migrations
	@echo "🗄️ Running database migrations..."
	@if [ -f ".venv/bin/alembic" ]; then \
		.venv/bin/alembic upgrade head; \
	else \
		echo "❌ Alembic not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

db-reset: ## Reset database (WARNING: This will delete all data!)
	@echo "⚠️  Resetting database (this will delete all data!)..."
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	@docker compose down -v
	@docker compose up -d
	@sleep 10
	@$(MAKE) db-migrate

# =============================================================================
# UTILITY TARGETS
# =============================================================================

logs: ## Show application logs
	@echo "📋 Showing application logs..."
	@tail -f logs/app.log 2>/dev/null || echo "No log file found"

status: ## Show system status
	@echo "📊 System Status"
	@echo "==============="
	@echo "Docker services:"
	@docker compose ps
	@echo ""
	@echo "Python environment:"
	@if [ -f ".venv/bin/python" ]; then \
		echo "✅ Virtual environment exists"; \
		.venv/bin/python --version; \
	else \
		echo "❌ Virtual environment not found"; \
	fi
	@echo ""
	@echo "Node.js environment:"
	@if [ -d "web/node_modules" ]; then \
		echo "✅ Node modules installed"; \
		node --version; \
		npm --version; \
	else \
		echo "❌ Node modules not installed"; \
	fi

# =============================================================================
# BOOTSTRAP SCRIPTS
# =============================================================================

bootstrap: ## Run bootstrap script for current OS
	@echo "🚀 Running bootstrap script..."
	@if [ "$$(uname)" = "Darwin" ] || [ "$$(uname)" = "Linux" ]; then \
		chmod +x scripts/bootstrap.sh && ./scripts/bootstrap.sh; \
	elif [ "$$(uname)" = "MINGW"* ] || [ "$$(uname)" = "CYGWIN"* ]; then \
		powershell -ExecutionPolicy Bypass -File scripts/bootstrap.ps1; \
	else \
		echo "❌ Unsupported operating system"; \
		exit 1; \
	fi

# =============================================================================
# DOCUMENTATION
# =============================================================================

docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@if [ -f ".venv/bin/sphinx-build" ]; then \
		.venv/bin/sphinx-build -b html docs/ docs/_build/html/; \
	else \
		echo "❌ Sphinx not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation..."
	@cd docs/_build/html && python3 -m http.server 8001

# =============================================================================
# SECURITY
# =============================================================================

security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	@if [ -f ".venv/bin/bandit" ]; then \
		.venv/bin/bandit -r . -x .venv,web; \
	else \
		echo "❌ Bandit not found. Run 'make setup-python' first."; \
		exit 1; \
	fi

# =============================================================================
# PERFORMANCE
# =============================================================================

benchmark: ## Run performance benchmarks
	@echo "⚡ Running benchmarks..."
	@if [ -f ".venv/bin/python" ]; then \
		.venv/bin/python -m pytest backend/tests/benchmarks/ -v; \
	else \
		echo "❌ Python virtual environment not found. Run 'make setup-python' first."; \
		exit 1; \
	fi
