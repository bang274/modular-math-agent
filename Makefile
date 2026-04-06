.PHONY: help dev dev-backend dev-frontend install install-backend install-frontend test lint format docker-up docker-down clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ─── Installation ───────────────────────────────────────────
install: install-backend install-frontend ## Install all dependencies

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm install

# ─── Development ────────────────────────────────────────────
dev: ## Run both backend and frontend (requires tmux or 2 terminals)
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"

dev-backend: ## Run FastAPI dev server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Run Vite dev server
	cd frontend && npm run dev

# ─── Testing ────────────────────────────────────────────────
test: ## Run all backend tests
	cd backend && python -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=html

test-frontend: ## Run frontend tests
	cd frontend && npm run test

# ─── Code Quality ───────────────────────────────────────────
lint: ## Lint backend code
	cd backend && python -m ruff check app/ tests/

format: ## Format backend code
	cd backend && python -m ruff format app/ tests/

typecheck: ## Type check frontend
	cd frontend && npx tsc --noEmit

# ─── Docker ─────────────────────────────────────────────────
docker-up: ## Start all services with Docker
	docker-compose up -d --build

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

# ─── Cleanup ────────────────────────────────────────────────
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/htmlcov backend/.coverage
	rm -rf frontend/dist frontend/node_modules/.vite
