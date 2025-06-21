# Core Engine Service

## Overzicht

De Core Engine Service is het centrale AI-verwerkingsonderdeel van het AI Voice Agent platform. Het coördineert tussen verschillende AI-services en beheert de hoofdconversatieflow.

## Functionaliteiten

- **AI Orchestratie**: Coördineert tussen verschillende AI-modellen en services
- **Conversatiebeheer**: Beheert conversatiesessies en context
- **Request Routing**: Routeert verzoeken naar de juiste AI-services
- **Response Aggregatie**: Verzamelt en verwerkt antwoorden van verschillende services

## Architectuur

### Hoofdcomponenten

1. **AIOrchestrator**: Centrale orchestratie-engine
2. **API Routes**: RESTful API endpoints
3. **Data Models**: Pydantic modellen voor verzoeken en antwoorden
4. **Configuration**: Service configuratiebeheer

### Service Communicatie

- **Inkomend**: REST API calls van API Gateway
- **Uitgaand**: HTTP calls naar Voice Module, Document Module
- **Database**: PostgreSQL voor persistentie
- **Cache**: Redis voor sessie- en contextbeheer
- **Vector DB**: Weaviate voor AI embeddings

## API Endpoints

### Hoofdroutes

- `GET /` - Service informatie
- `GET /health` - Health check
- `GET /api/v1/ai/status` - AI orchestrator status

### AI Processing

- `POST /api/v1/ai/process` - Algemene AI verwerking
- `POST /api/v1/ai/conversation` - Conversatiebeheer

## Configuratie

### Environment Variables

```env
# Service configuratie
SERVICE_NAME=core-engine
SERVICE_VERSION=1.0.0
DEBUG=false

# API configuratie
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/ai_voice_agent

# Redis
REDIS_URL=redis://redis:6379

# AI Models
OPENAI_API_KEY=your-openai-api-key
MODEL_NAME=gpt-4
MAX_TOKENS=2000
TEMPERATURE=0.7

# Vector Database
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=your-weaviate-key
```

## Installatie en Gebruik

### Lokale Ontwikkeling

1. **Installeer dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configureer environment**:
   ```bash
   cp .env.example .env
   # Bewerk .env met jouw configuratie
   ```

3. **Start de service**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

### Docker

1. **Build de container**:
   ```bash
   docker build -t core-engine .
   ```

2. **Run de container**:
   ```bash
   docker run -p 8000:8000 --env-file .env core-engine
   ```

### Docker Compose

```yaml
version: '3.8'
services:
  core-engine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/ai_voice_agent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
```

## Development

### Project Structuur

```
core-engine/
├── app/
│   ├── api/              # API routes en endpoints
│   ├── core/             # Business logic
│   ├── models/           # Data modellen
│   └── services/         # Service laag
├── tests/                # Test bestanden
├── Dockerfile            # Container configuratie
├── requirements.txt      # Python dependencies
└── README.md            # Deze documentatie
```

### Code Style

- Gebruik **Black** voor code formatting
- Gebruik **Pylint** voor linting
- Gebruik **Type hints** voor alle functies
- Schrijf **docstrings** voor alle publieke methoden

### Testing

```bash
# Run alle tests
pytest

# Run met coverage
pytest --cov=app

# Run specifieke test
pytest tests/test_orchestrator.py
```

## Monitoring

### Health Checks

De service biedt verschillende health check endpoints:

- `/health` - Basis service health
- `/api/v1/ai/status` - Uitgebreide AI orchestrator status

### Metrics

Prometheus metrics zijn beschikbaar op poort 9090:

- Service uptime
- Request counts en latency
- AI model usage statistieken
- Error rates

### Logging

Structured logging naar stdout in JSON formaat:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "core-engine",
  "message": "Processing AI request",
  "request_id": "uuid-here"
}
```

## Troubleshooting

### Veelvoorkomende Problemen

1. **Service start niet**:
   - Controleer environment variables
   - Verificeer database connectie
   - Check poort beschikbaarheid

2. **AI processing faalt**:
   - Verificeer OpenAI API key
   - Check model beschikbaarheid
   - Controleer rate limits

3. **High latency**:
   - Monitor database performance
   - Check Redis cache hit rates
   - Verify service communication

### Debug Mode

Enable debug mode voor uitgebreide logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork het project
2. Maak een feature branch
3. Commit je wijzigingen
4. Push naar de branch
5. Open een Pull Request

## License

Dit project valt onder de MIT License.# Core Engine Service

## Overzicht

De Core Engine Service is het centrale AI-verwerkingsonderdeel van het AI Voice Agent platform. Het coördineert tussen verschillende AI-services en beheert de hoofdconversatieflow.

## Functionaliteiten

- **AI Orchestratie**: Coördineert tussen verschillende AI-modellen en services
- **Conversatiebeheer**: Beheert conversatiesessies en context
- **Request Routing**: Routeert verzoeken naar de juiste AI-services
- **Response Aggregatie**: Verzamelt en verwerkt antwoorden van verschillende services

## Architectuur

### Hoofdcomponenten

1. **AIOrchestrator**: Centrale orchestratie-engine
2. **API Routes**: RESTful API endpoints
3. **Data Models**: Pydantic modellen voor verzoeken en antwoorden
4. **Configuration**: Service configuratiebeheer

### Service Communicatie

- **Inkomend**: REST API calls van API Gateway
- **Uitgaand**: HTTP calls naar Voice Module, Document Module
- **Database**: PostgreSQL voor persistentie
- **Cache**: Redis voor sessie- en contextbeheer
- **Vector DB**: Weaviate voor AI embeddings

## API Endpoints

### Hoofdroutes

- `GET /` - Service informatie
- `GET /health` - Health check
- `GET /api/v1/ai/status` - AI orchestrator status

### AI Processing

- `POST /api/v1/ai/process` - Algemene AI verwerking
- `POST /api/v1/ai/conversation` - Conversatiebeheer

## Configuratie

### Environment Variables

```env
# Service configuratie
SERVICE_NAME=core-engine
SERVICE_VERSION=1.0.0
DEBUG=false

# API configuratie
API_HOST=0.0.0.0
API_PORT=8000

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/ai_voice_agent

# Redis
REDIS_URL=redis://redis:6379

# AI Models
OPENAI_API_KEY=your-openai-api-key
MODEL_NAME=gpt-4
MAX_TOKENS=2000
TEMPERATURE=0.7

# Vector Database
WEAVIATE_URL=http://weaviate:8080
WEAVIATE_API_KEY=your-weaviate-key
```

## Installatie en Gebruik

### Lokale Ontwikkeling

1. **Installeer dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configureer environment**:
   ```bash
   cp .env.example .env
   # Bewerk .env met jouw configuratie
   ```

3. **Start de service**:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

### Docker

1. **Build de container**:
   ```bash
   docker build -t core-engine .
   ```

2. **Run de container**:
   ```bash
   docker run -p 8000:8000 --env-file .env core-engine
   ```

### Docker Compose

```yaml
version: '3.8'
services:
  core-engine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/ai_voice_agent
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
```

## Development

### Project Structuur

```
core-engine/
├── app/
│   ├── api/              # API routes en endpoints
│   ├── core/             # Business logic
│   ├── models/           # Data modellen
│   └── services/         # Service laag
├── tests/                # Test bestanden
├── Dockerfile            # Container configuratie
├── requirements.txt      # Python dependencies
└── README.md            # Deze documentatie
```

### Code Style

- Gebruik **Black** voor code formatting
- Gebruik **Pylint** voor linting
- Gebruik **Type hints** voor alle functies
- Schrijf **docstrings** voor alle publieke methoden

### Testing

```bash
# Run alle tests
pytest

# Run met coverage
pytest --cov=app

# Run specifieke test
pytest tests/test_orchestrator.py
```

## Monitoring

### Health Checks

De service biedt verschillende health check endpoints:

- `/health` - Basis service health
- `/api/v1/ai/status` - Uitgebreide AI orchestrator status

### Metrics

Prometheus metrics zijn beschikbaar op poort 9090:

- Service uptime
- Request counts en latency
- AI model usage statistieken
- Error rates

### Logging

Structured logging naar stdout in JSON formaat:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "core-engine",
  "message": "Processing AI request",
  "request_id": "uuid-here"
}
```

## Troubleshooting

### Veelvoorkomende Problemen

1. **Service start niet**:
   - Controleer environment variables
   - Verificeer database connectie
   - Check poort beschikbaarheid

2. **AI processing faalt**:
   - Verificeer OpenAI API key
   - Check model beschikbaarheid
   - Controleer rate limits

3. **High latency**:
   - Monitor database performance
   - Check Redis cache hit rates
   - Verify service communication

### Debug Mode

Enable debug mode voor uitgebreide logging:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork het project
2. Maak een feature branch
3. Commit je wijzigingen
4. Push naar de branch
5. Open een Pull Request

## License

Dit project valt onder de MIT License.