.PHONY: dev build test seed lint clean

## Run everything with Docker
up:
	docker-compose up --build

## Run backend locally
backend:
	cd backend && uvicorn main:app --reload --port 8000

## Run frontend locally
frontend:
	cd frontend && npm run dev

## Install all deps
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

## Seed the knowledge base into ChromaDB
seed:
	cd backend && python ../scripts/seed_vectordb.py

## Run all tests
test:
	cd backend && pytest ../tests/ -v --cov=. --cov-report=html

## Lint
lint:
	cd backend && ruff check .
	cd frontend && npm run lint

## Clean build artifacts
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf frontend/dist htmlcov .pytest_cache
