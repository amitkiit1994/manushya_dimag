# Makefile for Manushya.ai

.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  dev         - Start development server"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code"
	@echo "  clean       - Clean up generated files"
	@echo "  docker-build- Build Docker images"
	@echo "  docker-up   - Start Docker services"
	@echo "  docker-down - Stop Docker services"
	@echo "  migrate     - Run database migrations"

# Install dependencies
install:
	pip install -e ".[dev]"

# Start development server
dev:
	uvicorn manushya.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest tests/ -v --cov=manushya --cov-report=term-missing

# Run tests with coverage report
test-cov:
	pytest tests/ -v --cov=manushya --cov-report=html --cov-report=term-missing

# Run linting
lint:
	ruff check manushya/
	mypy manushya/

# Format code
format:
	black manushya/
	ruff check --fix manushya/

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .mypy_cache/

# Build Docker images
docker-build:
	docker-compose build

# Start Docker services
docker-up:
	docker-compose up -d

# Stop Docker services
docker-down:
	docker-compose down

# Run database migrations
migrate:
	docker-compose exec api alembic upgrade head

# Create new migration
migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(message)"

# Rollback migration
migrate-rollback:
	docker-compose exec api alembic downgrade -1

# Initialize database
init-db:
	docker-compose exec api python -c "from manushya.db.database import init_db; import asyncio; asyncio.run(init_db())"

# Create default policies
init-policies:
	docker-compose exec api python -c "from manushya.db.database import AsyncSessionLocal; from manushya.core.policy_engine import create_default_policies; import asyncio; asyncio.run(create_default_policies(AsyncSessionLocal()))"

# View logs
logs:
	docker-compose logs -f

# View API logs
logs-api:
	docker-compose logs -f api

# View database logs
logs-db:
	docker-compose logs -f postgres

# View Redis logs
logs-redis:
	docker-compose logs -f redis

# View Celery logs
logs-celery:
	docker-compose logs -f celery-worker

# Health check
health:
	curl -f http://localhost:8000/health

# API docs
docs:
	open http://localhost:8000/v1/docs

# Metrics
metrics:
	curl http://localhost:8000/metrics

# Celery monitor
flower:
	open http://localhost:5555

# Backup database
backup:
	docker-compose exec postgres pg_dump -U manushya manushya > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Restore database
restore:
	docker-compose exec -T postgres psql -U manushya manushya < $(file)

# Shell into API container
shell:
	docker-compose exec api bash

# Shell into database
db-shell:
	docker-compose exec postgres psql -U manushya -d manushya

# Restart services
restart:
	docker-compose restart

# Full setup (install, build, up, migrate, init)
setup: install docker-build docker-up
	@echo "Waiting for services to start..."
	@sleep 10
	@echo "Running migrations..."
	@make migrate
	@echo "Initializing database..."
	@make init-db
	@echo "Creating default policies..."
	@make init-policies
	@echo "Setup complete! Access the API at http://localhost:8000/v1/docs"

# Development setup
dev-setup: install
	@echo "Development setup complete!"
	@echo "Run 'make dev' to start the development server" 