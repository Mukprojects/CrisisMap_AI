.PHONY: help install install-dev test test-cov lint format clean build run docker-build docker-run setup-dev

# Default target
help:
	@echo "CrisisMap AI - Development Commands"
	@echo "=================================="
	@echo "install          Install production dependencies"
	@echo "install-dev      Install development dependencies"
	@echo "setup-dev        Complete development setup (install + pre-commit)"
	@echo "test             Run tests"
	@echo "test-cov         Run tests with coverage"
	@echo "lint             Run linting checks"
	@echo "format           Format code"
	@echo "clean            Clean build artifacts"
	@echo "build            Build package"
	@echo "run              Run the application"
	@echo "run-dev          Run the application in development mode"
	@echo "docker-build     Build Docker image"
	@echo "docker-run       Run Docker container"
	@echo "migrate          Run database migrations"
	@echo "seed-data        Load sample data"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,monitoring,deployment]"

setup-dev: install-dev
	pre-commit install
	@echo "Development environment setup complete!"

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=crisismap_ai --cov-report=html --cov-report=term-missing

test-watch:
	pytest-watch tests/ -v

# Code Quality
lint:
	black --check crisismap_ai/ tests/
	isort --check-only crisismap_ai/ tests/
	flake8 crisismap_ai/ tests/
	mypy crisismap_ai/
	bandit -r crisismap_ai/

format:
	black crisismap_ai/ tests/
	isort crisismap_ai/ tests/

security-check:
	bandit -r crisismap_ai/
	safety check

# Build and Clean
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

# Development
run:
	cd crisismap_ai && python main.py server

run-dev:
	cd crisismap_ai && uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

run-api:
	cd crisismap_ai && python run_api.py

# Database
migrate:
	cd crisismap_ai && python main.py --action setup

seed-data:
	cd crisismap_ai && python main.py --action ingest --dataset all --limit 1000

create-index:
	cd crisismap_ai && python create_vector_index.py

# Docker
docker-build:
	docker build -t crisismap-ai:latest .

docker-run:
	docker run -p 8000:8000 --env-file .env crisismap-ai:latest

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# Documentation
docs-serve:
	mkdocs serve

docs-build:
	mkdocs build

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	# Add staging deployment commands here

deploy-prod:
	@echo "Deploying to production..."
	# Add production deployment commands here

# Monitoring
logs:
	docker-compose logs -f app

health-check:
	curl -f http://localhost:8000/health || exit 1

# Environment
env-example:
	cp crisismap_ai/.env.example crisismap_ai/.env
	@echo "Created .env file from example. Please update with your credentials."

# All-in-one commands
fresh-install: clean install-dev setup-dev
	@echo "Fresh installation complete!"

quick-start: fresh-install env-example
	@echo "Quick start setup complete! Update .env file and run 'make run'"