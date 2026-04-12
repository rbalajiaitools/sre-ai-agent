# SRE AI Agent Platform

Enterprise-grade multi-tenant SaaS platform for automated incident investigation and resolution using AI agents.

## Features

- **Multi-Cloud Support**: AWS adapter with extensible framework for Azure, GCP
- **ServiceNow Integration**: Automated incident polling and investigation
- **AI-Powered Agents**: Specialized agents for metrics, logs, infrastructure, code, and security analysis
- **Knowledge Graph**: Neo4j-based topology and incident memory
- **LLM Integration**: Support for OpenAI, Azure OpenAI, and Anthropic
- **Investigation Orchestration**: LangGraph-based workflow engine

## Quick Start

### Prerequisites

- Python 3.12+
- AWS credentials configured
- ServiceNow instance (optional)
- Azure OpenAI or OpenAI API key

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Application
APP_NAME=sre-agent
APP_ENV=development
LOG_LEVEL=INFO

# LLM Provider (choose one)
LLM_PROVIDER=azure  # or openai, anthropic
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# ServiceNow (optional)
SERVICENOW_INSTANCE_URL=https://your-instance.service-now.com
SERVICENOW_USERNAME=your-username
SERVICENOW_PASSWORD=your-password

# AWS
AWS_DEFAULT_REGION=us-east-1

# Databases (optional for full features)
DATABASE_URL=sqlite+aiosqlite:///./sre_agent.db
REDIS_URL=redis://localhost:6379/0
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
```

### Run Application

```bash
# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Simulation Test

```bash
# Test with real AWS Lambda and ServiceNow
python simulation_test.py
```

## API Endpoints

- `GET /api/v1/health` - Health check
- `GET /api/v1/docs` - Swagger UI documentation
- `POST /api/v1/investigations` - Start investigation
- `GET /api/v1/investigations/{id}` - Get investigation status
- `GET /api/v1/incidents` - List incidents

## Architecture

```
app/
├── adapters/          # Cloud provider adapters (AWS, Azure, GCP)
├── agents/            # Specialized AI agents
├── api/               # FastAPI routes
├── connectors/        # External system connectors (ServiceNow)
├── core/              # Core utilities (config, logging, LLM)
├── knowledge/         # Knowledge graph and memory
├── models/            # Pydantic models
└── orchestration/     # Investigation workflow orchestration
```

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/
```

## Production Deployment

### Using Docker

```bash
# Build image
docker build -t sre-agent .

# Run container
docker run -p 8000:8000 --env-file .env sre-agent
```

### Using Docker Compose

```bash
docker-compose up -d
```

## License

Proprietary - All rights reserved

## Support

For issues and questions, please contact the development team.
