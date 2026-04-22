#!/bin/bash

# CloudScore ASTRA AI - Phase 1 Setup Script

set -e

echo "=== CloudScore ASTRA AI - Phase 1 Setup ==="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "✓ .env file created. Please update it with your configuration."
else
    echo "✓ .env file already exists"
fi

# Start infrastructure services
echo ""
echo "Starting infrastructure services..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "Waiting for services to be healthy..."
sleep 10

# Check PostgreSQL
echo "Checking PostgreSQL..."
until docker exec astra-postgres pg_isready -U astra_user > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done
echo "✓ PostgreSQL is ready"

# Check Redis
echo "Checking Redis..."
until docker exec astra-redis redis-cli ping > /dev/null 2>&1; do
    echo "  Waiting for Redis..."
    sleep 2
done
echo "✓ Redis is ready"

# Check Kafka
echo "Checking Kafka..."
sleep 5
until docker exec astra-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092 > /dev/null 2>&1; do
    echo "  Waiting for Kafka..."
    sleep 2
done
echo "✓ Kafka is ready"

# Check Temporal
echo "Checking Temporal..."
sleep 5
echo "✓ Temporal is starting (may take a minute)"

# Create Kafka topics
echo ""
echo "Creating Kafka topics..."
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic alerts.ingested --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic investigations.requested --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic investigations.completed --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic notifications.dispatch --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
echo "✓ Kafka topics created"

# Install shared libraries
echo ""
echo "Installing shared libraries..."
cd shared-libs
pip install -e . > /dev/null 2>&1
echo "✓ Shared libraries installed"

# Run database migrations
echo ""
echo "Running database migrations..."
alembic upgrade head
echo "✓ Database migrations completed"

cd ..

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Infrastructure services are running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Kafka: localhost:9092"
echo "  - Temporal: localhost:7233"
echo "  - Temporal UI: http://localhost:8233"
echo ""
echo "Next steps:"
echo "  1. Update .env with your configuration"
echo "  2. Proceed to Phase 2 service implementation"
echo ""
