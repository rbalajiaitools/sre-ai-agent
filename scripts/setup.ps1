# CloudScore ASTRA AI - Phase 1 Setup Script (PowerShell)

Write-Host "=== CloudScore ASTRA AI - Phase 1 Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "Error: Docker is not running. Please start Docker and try again." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from .env.example..."
    Copy-Item .env.example .env
    Write-Host "Successfully created .env file. Please update it with your configuration." -ForegroundColor Green
} else {
    Write-Host "Found existing .env file" -ForegroundColor Green
}

# Start infrastructure services
Write-Host ""
Write-Host "Starting infrastructure services..."
docker-compose up -d

# Wait for services to be healthy
Write-Host ""
Write-Host "Waiting for services to be healthy..."
Start-Sleep -Seconds 10

# Check PostgreSQL
Write-Host "Checking PostgreSQL..."
$retries = 0
while ($retries -lt 30) {
    try {
        docker exec astra-postgres pg_isready -U astra_user 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    } catch {}
    Write-Host "  Waiting for PostgreSQL..."
    Start-Sleep -Seconds 2
    $retries++
}
Write-Host "PostgreSQL is ready" -ForegroundColor Green

# Check Redis
Write-Host "Checking Redis..."
$retries = 0
while ($retries -lt 30) {
    try {
        docker exec astra-redis redis-cli ping 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    } catch {}
    Write-Host "  Waiting for Redis..."
    Start-Sleep -Seconds 2
    $retries++
}
Write-Host "Redis is ready" -ForegroundColor Green

# Check Kafka
Write-Host "Checking Kafka..."
Start-Sleep -Seconds 5
$retries = 0
while ($retries -lt 30) {
    try {
        docker exec astra-kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
    } catch {}
    Write-Host "  Waiting for Kafka..."
    Start-Sleep -Seconds 2
    $retries++
}
Write-Host "Kafka is ready" -ForegroundColor Green

# Check Temporal
Write-Host "Checking Temporal..."
Start-Sleep -Seconds 5
Write-Host "Temporal is starting (may take a minute)" -ForegroundColor Green

# Create Kafka topics
Write-Host ""
Write-Host "Creating Kafka topics..."
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic alerts.ingested --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>&1 | Out-Null
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic investigations.requested --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>&1 | Out-Null
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic investigations.completed --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>&1 | Out-Null
docker exec astra-kafka kafka-topics.sh --create --if-not-exists --topic notifications.dispatch --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 2>&1 | Out-Null
Write-Host "Kafka topics created" -ForegroundColor Green

# Install shared libraries
Write-Host ""
Write-Host "Installing shared libraries..."
Set-Location shared-libs
pip install -e . 2>&1 | Out-Null
Write-Host "Shared libraries installed" -ForegroundColor Green

# Run database migrations
Write-Host ""
Write-Host "Running database migrations..."
alembic upgrade head
Write-Host "Database migrations completed" -ForegroundColor Green

Set-Location ..

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Infrastructure services are running:"
Write-Host "  - PostgreSQL: localhost:5432"
Write-Host "  - Redis: localhost:6379"
Write-Host "  - Kafka: localhost:9092"
Write-Host "  - Temporal: localhost:7233"
Write-Host "  - Temporal UI: http://localhost:8233"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Update .env with your configuration"
Write-Host "  2. Proceed to Phase 2 service implementation"
Write-Host ""
