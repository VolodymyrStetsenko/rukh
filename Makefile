.PHONY: help install up down logs test lint e2e seed-demo clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	@echo "Installing dependencies..."
	cd apps/web && pnpm install
	cd apps/api-gateway && pip3 install -r requirements.txt
	cd services/analysis-planner && pip3 install -r requirements.txt
	cd services/test-synth && pip3 install -r requirements.txt
	cd services/symbolic-runner && pip3 install -r requirements.txt
	cd services/reporter && pip3 install -r requirements.txt
	cd services/static-intel && cargo build
	cd services/bytecode-intel && cargo build
	cd services/fuzz-runner && cargo build
	cd services/attack-graph && cargo build
	@echo "Dependencies installed successfully!"

up: ## Start all services with Docker Compose
	@echo "Starting RUKH services..."
	docker-compose -f deployments/docker/docker-compose.yml up -d
	@echo "Services started! Web UI: http://localhost:3000"

down: ## Stop all services
	@echo "Stopping RUKH services..."
	docker-compose -f deployments/docker/docker-compose.yml down
	@echo "Services stopped!"

logs: ## Show logs from all services
	docker-compose -f deployments/docker/docker-compose.yml logs -f

test: ## Run all tests
	@echo "Running tests..."
	cd apps/web && pnpm test
	cd apps/api-gateway && pytest
	cd services/analysis-planner && pytest
	cd services/static-intel && cargo test
	cd services/bytecode-intel && cargo test
	cd services/fuzz-runner && cargo test
	cd services/attack-graph && cargo test
	@echo "All tests passed!"

lint: ## Run linters
	@echo "Running linters..."
	cd apps/web && pnpm lint
	cd apps/api-gateway && ruff check . && mypy .
	cd services/analysis-planner && ruff check . && mypy .
	cd services/static-intel && cargo clippy
	cd services/bytecode-intel && cargo clippy
	cd services/fuzz-runner && cargo clippy
	cd services/attack-graph && cargo clippy
	@echo "Linting complete!"

e2e: ## Run end-to-end tests
	@echo "Running E2E tests..."
	cd bench && ./run-benchmarks.sh
	@echo "E2E tests complete!"

seed-demo: ## Seed demo vulnerable contracts
	@echo "Seeding demo contracts..."
	cd integrations/foundry && forge install
	cd integrations/foundry && forge build
	@echo "Demo contracts seeded!"

clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "target" -exec rm -rf {} +
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".next" -exec rm -rf {} +
	find . -type d -name "out" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	@echo "Clean complete!"

build: ## Build all services
	@echo "Building services..."
	cd apps/web && pnpm build
	cd services/static-intel && cargo build --release
	cd services/bytecode-intel && cargo build --release
	cd services/fuzz-runner && cargo build --release
	cd services/attack-graph && cargo build --release
	@echo "Build complete!"

dev-web: ## Start web development server
	cd apps/web && pnpm dev

dev-api: ## Start API gateway development server
	cd apps/api-gateway && uvicorn main:app --reload --host 0.0.0.0 --port 8000

