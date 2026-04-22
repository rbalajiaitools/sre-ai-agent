.PHONY: help setup start stop restart logs clean install-libs migrate test

help:
	@echo "CloudScore ASTRA AI - Phase 1 Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Initial setup (start services, install libs, run migrations)"
	@echo "  make install-libs   - Install shared libraries"
	@echo ""
	@echo "Infrastructure:"
	@echo "  make start          - Start all infrastructure services"
	@echo "  make stop           - Stop all infrastructure services"
	@echo "  make restart        - Restart all infrastructure services"
	@echo "  make logs           - View logs from all services"
	@echo "  make clean          - Stop services and remove volumes"
	@echo ""
	@echo "Database:"
	@echo "  make migrate        - Run database migrations"
	@echo "  make migrate-create - Create a new migration"
	@echo "  make migrate-down   - Rollback last migration"
	@echo ""
	@echo "Development:"
	@echo "  make test           - Run tests"
	@echo "  make format         - Format code with black"
	@echo "  make lint           - Lint code with ruff"
	@echo ""
	@echo "Kafka:"
	@echo "  make kafka-topics   - List Kafka topics"
	@echo "  make kafka-create   - Create default Kafka topics"
	@echo ""

setup:
	@echo "Running setup..."
	@bash scripts/setup.sh

start:
	@echo "Starting infrastructure services..."
	docker-compose up -d
	@echo "Services started. Use 'make logs' to view logs."

stop:
	@echo "Stopping infrastructure services..."
	docker-compose down

restart:
	@echo "Restarting infrastructure services..."
	docker-compose restart

logs:
	docker-compose logs -f

clean:
	@echo "Stopping services and removing volumes..."
	docker-compose down -v
	@echo "Cleaned up."

install-libs:
	@echo "Installing shared libraries..."
	cd shared-libs && pip install -e .
	@echo "Shared libraries installed."

migrate:
	@echo "Running database migrations..."
	cd shared-libs && alembic upgrade head
	@echo "Migrations completed."

migrate-create:
	@echo "Creating new migration..."
	@read -p "Migration message: " msg; \
	cd shared-libs && alembic revision --autogenerate -m "$$msg"

migrate-down:
	@echo "Rolling back last migration..."
	cd shared-libs && alembic downgrade -1

test:
	@echo "Running tests..."
	cd shared-libs && pytest

format:
	@echo "Formatting code..."
	cd shared-libs && black shared/

lint:
	@echo "Linting code..."
	cd shared-libs && ruff check shared/

kafka-topics:
	@echo "Kafka topics:"
	docker exec astra-kafka kafka-topics.sh --list --bootstrap-server localhost:9092

kafka-create:
	@echo "Creating Kafka topics..."
	docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic alerts.ingested --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
	docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic investigations.requested --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
	docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic investigations.completed --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
	docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic notifications.dispatch --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
	@echo "Topics created."

health:
	@echo "Checking service health..."
	@echo -n "PostgreSQL: "
	@docker exec astra-postgres pg_isready -U astra_user && echo "✓" || echo "✗"
	@echo -n "Redis: "
	@docker exec astra-redis redis-cli ping && echo "✓" || echo "✗"
	@echo -n "Kafka: "
	@docker exec astra-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1 && echo "✓" || echo "✗"
	@echo "Temporal UI: http://localhost:8233"
