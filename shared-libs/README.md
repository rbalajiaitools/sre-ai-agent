# CloudScore ASTRA AI - Shared Libraries

Shared libraries for CloudScore ASTRA AI microservices.

## Installation

```bash
pip install -e .
```

## Components

### Database
- SQLAlchemy 2.0 async models
- Alembic migrations
- Connection pooling
- Session management

### Models
All database models with relationships:
- Tenant, User
- Investigation, Hypothesis, EvidenceItem
- Alert, Incident
- Action, ActionExecution
- Policy, PolicyEvaluation
- Connector, ConnectorExecution
- AuditLog
- Notification
- KnowledgeBase, KnowledgeEmbedding (with pgvector)

### Events
Kafka event schemas and utilities:
- Event types: Alert, Investigation, Notification, Action
- EventProducer for publishing events
- EventConsumer for consuming events

### Authentication
- JWT token creation and verification
- Password hashing with bcrypt
- FastAPI middleware
- Role-based access control

### Logging
- Structured logging with structlog
- JSON and console formats
- Context binding for request tracking

### Configuration
- Pydantic settings for all services
- Environment variable support
- Type-safe configuration

## Usage

### Database

```python
from shared.database import init_db, get_db_session
from shared.config import get_settings

settings = get_settings()
db_manager = init_db(settings.database)

# Use in FastAPI
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@app.get("/items")
async def get_items(db: AsyncSession = Depends(get_db_session)):
    result = await db.execute(select(Item))
    return result.scalars().all()
```

### Events

```python
from shared.events import EventProducer, AlertEvent, EventType
from shared.config import get_settings

settings = get_settings()

# Publish event
with EventProducer(settings.kafka) as producer:
    event = AlertEvent(
        event_id="123",
        event_type=EventType.ALERT_INGESTED,
        tenant_id="tenant-1",
        alert_id="alert-1",
        severity="high",
        title="High CPU usage",
        source="cloudwatch",
        fingerprint="abc123"
    )
    await producer.publish("alerts.ingested", event)
```

### Authentication

```python
from fastapi import Depends
from shared.auth import get_current_user, require_role

@app.get("/admin")
async def admin_endpoint(user: dict = Depends(require_role("admin"))):
    return {"message": "Admin access granted"}
```

### Logging

```python
from shared.logging import setup_logging, get_logger, bind_context

settings = get_settings()
setup_logging(settings.logging)

logger = get_logger(__name__)

# Bind context
bind_context(request_id="123", tenant_id="tenant-1")

logger.info("processing_request", user_id="user-1")
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black shared/
ruff check shared/
```

### Type Checking

```bash
mypy shared/
```
