.PHONY: init run-dev stop lint test clean docker-check

# Environment variables
COMPOSE_FILE = docker-compose.yml
COMPOSE_DEV_FILE = docker-compose.dev.yml

init:
	@echo "Initializing development environment..."
	python -m pip install --upgrade pip
	pip install uv
	uv pip install -r services/control-plane/requirements.txt --system || uv pip install -r services/control-plane/requirements.txt

run-dev:
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) up --build

stop:
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) down

docker-check:
	docker compose -f $(COMPOSE_FILE) config --quiet

lint:
	@echo "Running lint and type checks..."
	ruff check services/control-plane
	mypy services/control-plane

test:
	@echo "Running test suite..."
	pytest tests/

clean:
	docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV_FILE) down -v
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
