.PHONY: help install setup-hooks run lint format check test clean pre-commit notebook db-upgrade db-downgrade db-current db-history db-revision db-reset

# Default target - show help
.DEFAULT_GOAL := help

##@ Setup

install: ## Install project dependencies
	@echo "Installing dependencies with uv..."
	uv sync
	@echo "✅ Dependencies installed successfully"

setup-hooks: ## Install git hooks for commit message validation and code quality
	@echo "Installing git hooks..."
	uv run pre-commit install --hook-type commit-msg
	uv run pre-commit install
	git config commit.template .gitmessage
	@echo "✅ Git hooks installed successfully"

setup: install setup-hooks ## Complete project setup (install dependencies + git hooks)
	@echo "✅ Project setup complete!"
	@echo "You can now start developing. Run 'make help' to see available commands."

##@ Development

http_serve: ## Run the HTTP backend application
	@echo "Running api application..."
	uv run fastapi dev tabapi/http_serve.py

fmt: ## Format code with ruff
	@echo "Formatting code..."
	uv run ruff format .
	@echo "✅ Code formatted"

format: fmt ## Alias for fmt

lint: ## Run linter (ruff check)
	@echo "Running linter..."
	uv run ruff check . --fix
	@echo "✅ Linting complete"

check: ## Run all code quality checks (format + lint)
	@echo "Running code quality checks..."
	uv run ruff format .
	uv run ruff check . --fix
	@echo "✅ All checks passed"

##@ Database

db-upgrade: ## Run database migrations to latest version
	@echo "Running database migrations..."
	uv run alembic upgrade head
	@echo "✅ Database upgraded to latest version"

db-downgrade: ## Rollback database migration by one version
	@echo "Rolling back database migration..."
	uv run alembic downgrade -1
	@echo "✅ Database rolled back by one version"

db-current: ## Show current database migration version
	@echo "Current database version:"
	uv run alembic current

db-history: ## Show database migration history
	@echo "Migration history:"
	uv run alembic history

db-revision: ## Create new migration (usage: make db-revision msg="description")
	@echo "Creating new migration..."
	uv run alembic revision --autogenerate -m "$(msg)"
	@echo "✅ Migration created"

db-reset: ## Reset database (downgrade to base, then upgrade to head)
	@echo "Resetting database..."
	uv run alembic downgrade base
	uv run alembic upgrade head
	@echo "✅ Database reset complete"

##@ Testing

test: ## Run tests
	@echo "Running tests..."
	uv run pytest
	@echo "✅ Tests complete"

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	uv run pytest --cov=tabapi --cov-report=term-missing --cov-report=html
	@echo "✅ Coverage report generated in htmlcov/"

##@ Git & Quality

pre-commit: ## Run pre-commit hooks on all files
	@echo "Running pre-commit hooks on all files..."
	uv run pre-commit run --all-files

pre-commit-update: ## Update pre-commit hooks to latest versions
	@echo "Updating pre-commit hooks..."
	uv run pre-commit autoupdate
	@echo "✅ Pre-commit hooks updated"

commit-check: ## Validate last commit message
	@echo "Checking last commit message..."
	uv run gitlint --commits HEAD

##@ Cleanup

clean: ## Clean up generated files and caches
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	rm -rf htmlcov .coverage 2>/dev/null || true
	@echo "✅ Cleanup complete"

clean-all: clean ## Deep clean (including virtual environment)
	@echo "Performing deep clean..."
	rm -rf .venv
	rm -rf uv.lock
	@echo "✅ Deep clean complete. Run 'make install' to reinstall."

##@ Information

version: ## Show Python and uv versions
	@echo "Python version:"
	@uv run python --version
	@echo "\nuv version:"
	@uv --version
	@echo "\nProject version:"
	@grep "^version" pyproject.toml

deps: ## Show installed dependencies
	@echo "Installed packages:"
	@uv pip list

notebook: ## Run Jupyter Notebook
	@echo "Starting Jupyter Notebook..."
	uv run jupyter notebook

##@ Help

help: ## Display this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
