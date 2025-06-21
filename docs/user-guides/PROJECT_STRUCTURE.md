# =============================================================================

# ENTERPRISE AI VOICE AGENT PLATFORM - PROJECT STRUCTURE SPECIFICATION

# =============================================================================

# Dit document definieert de EXACTE bestandsstructuur die ALTIJD gevolgd moet worden

# Elke nieuwe file moet conform deze structuur worden aangemaakt

## 🏗️ ROOT LEVEL STRUCTURE

```
ai-voice-agent-v3/                          # Project root
├── .github/                                # GitHub workflows & templates
│   ├── workflows/                          # CI/CD pipelines
│   ├── ISSUE_TEMPLATE/                     # Issue templates
│   └── pull_request_template.md           # PR template
├── docs/                                   # Project documentation
│   ├── api/                               # API documentation
│   ├── architecture/                      # System architecture docs
│   ├── deployment/                        # Deployment guides
│   └── user-guides/                       # User documentation
├── services/                              # Microservices (MAIN CODE)
│   ├── realtime-voice/                    # Voice AI service
│   ├── api-gateway/                       # API Gateway service
│   ├── document-module/                   # Document processing
│   ├── core-engine/                       # Core AI engine
│   └── dashboard/                         # Admin dashboard
├── shared/                                # Shared libraries & configs
│   ├── config/                           # Shared configuration
│   ├── utils/                            # Shared utilities
│   └── schemas/                          # Shared data schemas
├── infrastructure/                        # Infrastructure as Code
│   ├── docker/                           # Docker configurations
│   ├── kubernetes/                       # K8s manifests
│   ├── terraform/                        # Infrastructure code
│   └── monitoring/                       # Monitoring configs
├── scripts/                              # Build & deployment scripts
│   ├── build/                           # Build scripts
│   ├── deploy/                          # Deployment scripts
│   └── maintenance/                     # Maintenance scripts
├── tests/                                # Integration & E2E tests
│   ├── integration/                     # Cross-service tests
│   ├── e2e/                            # End-to-end tests
│   └── performance/                     # Performance tests
├── storage/                              # Persistent data (dev only)
└── .venv/                               # Python virtual environment
```

## 🎯 SERVICE LEVEL STRUCTURE (per microservice)

```
services/realtime-voice/                    # Service root
├── src/                                   # Source code (CORE)
│   ├── __init__.py                       # Package init
│   ├── main.py                          # Application entry point
│   ├── config/                          # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py                   # Environment settings
│   │   ├── database.py                   # Database config
│   │   └── logging.py                    # Logging config
│   ├── api/                             # API layer
│   │   ├── __init__.py
│   │   ├── routes/                       # API routes
│   │   ├── middleware/                   # Custom middleware
│   │   └── dependencies.py              # FastAPI dependencies
│   ├── core/                            # Business logic
│   │   ├── __init__.py
│   │   ├── audio/                        # Audio processing
│   │   ├── ai/                          # AI model integration
│   │   ├── conversation/                 # Conversation management
│   │   └── websocket/                    # WebSocket handling
│   ├── models/                          # Data models
│   │   ├── __init__.py
│   │   ├── database/                     # Database models
│   │   ├── api/                         # API models (Pydantic)
│   │   └── ai/                          # AI model schemas
│   ├── services/                        # Service layer
│   │   ├── __init__.py
│   │   ├── audio_service.py             # Audio processing service
│   │   ├── ai_service.py                # AI integration service
│   │   └── session_service.py           # Session management
│   ├── repository/                      # Data access layer
│   │   ├── __init__.py
│   │   ├── database/                     # Database repositories
│   │   └── cache/                       # Cache repositories
│   └── utils/                           # Utility functions
│       ├── __init__.py
│       ├── validators.py                # Data validation
│       ├── exceptions.py                # Custom exceptions
│       └── helpers.py                   # Helper functions
├── tests/                               # Service-specific tests
│   ├── __init__.py
│   ├── unit/                           # Unit tests
│   ├── integration/                    # Integration tests
│   └── fixtures/                       # Test fixtures
├── migrations/                          # Database migrations
│   └── versions/                       # Migration versions
├── static/                             # Static files
│   ├── css/                           # Stylesheets
│   ├── js/                            # JavaScript files
│   └── images/                        # Images
├── templates/                          # HTML templates
├── config/                             # Service configuration
│   ├── development.yaml               # Dev environment config
│   ├── staging.yaml                   # Staging environment config
│   └── production.yaml                # Production environment config
├── scripts/                           # Service-specific scripts
│   ├── setup.py                       # Service setup
│   ├── migrate.py                     # Database migration
│   └── seed.py                        # Data seeding
├── docs/                              # Service documentation
│   ├── api.md                         # API documentation
│   ├── deployment.md                  # Deployment guide
│   └── troubleshooting.md             # Troubleshooting guide
├── monitoring/                        # Monitoring & observability
│   ├── prometheus/                    # Prometheus configs
│   ├── grafana/                       # Grafana dashboards
│   └── alerts/                        # Alert configurations
├── requirements/                      # Dependencies
│   ├── base.txt                       # Base requirements
│   ├── development.txt                # Development requirements
│   ├── production.txt                 # Production requirements
│   └── testing.txt                    # Testing requirements
├── .env.example                       # Environment template
├── .dockerignore                      # Docker ignore rules
├── Dockerfile                         # Container definition
├── docker-compose.yml                # Local development
├── docker-compose.prod.yml           # Production compose
├── pyproject.toml                     # Python project config
├── README.md                          # Service documentation
└── .gitignore                        # Git ignore rules
```

## 📋 FILE NAMING CONVENTIONS

### Python Files

- **Modules**: `snake_case.py` (e.g., `audio_processor.py`)
- **Classes**: `PascalCase` (e.g., `AudioProcessor`)
- **Functions**: `snake_case()` (e.g., `process_audio()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_AUDIO_LENGTH`)

### Configuration Files

- **Environment**: `.env`, `.env.example`, `.env.production`
- **Docker**: `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml`
- **Config**: `settings.yaml`, `logging.yaml`, `database.yaml`

### Documentation Files

- **Markdown**: `UPPERCASE.md` for important docs (README.md, CHANGELOG.md)
- **API docs**: `api.md`, `endpoints.md`
- **Guides**: `deployment-guide.md`, `user-guide.md`

### Test Files

- **Unit tests**: `test_*.py` (e.g., `test_audio_processor.py`)
- **Integration**: `integration_test_*.py`
- **E2E tests**: `e2e_test_*.py`

## 🚀 DEPLOYMENT & INFRASTRUCTURE

### Container Structure

```
/app/                                   # Container working directory
├── src/                               # Application source
├── static/                            # Static assets
├── templates/                         # Templates
├── config/                            # Runtime configuration
└── logs/                              # Application logs
```

### Kubernetes Structure

```
infrastructure/kubernetes/
├── namespace.yaml                     # Kubernetes namespace
├── services/                          # Service definitions
├── deployments/                       # Deployment manifests
├── configmaps/                        # Configuration maps
├── secrets/                           # Secret definitions
├── ingress/                           # Ingress controllers
└── monitoring/                        # Monitoring resources
```

## 🔧 DEVELOPMENT WORKFLOW

### When creating NEW files:

1. **Identify the PURPOSE** of the file
2. **Determine the LAYER** (api, core, models, services, etc.)
3. **Follow the EXACT path** from this structure
4. **Use proper NAMING conventions**
5. **Add appropriate DOCSTRINGS and COMMENTS**

### When modifying EXISTING files:

1. **Respect the current structure**
2. **Don't move files without updating imports**
3. **Keep related functionality together**
4. **Maintain consistency with existing patterns**

## 📊 QUALITY STANDARDS

### Every Python file MUST have:

- Proper module docstring
- Type hints for all functions
- Error handling
- Logging where appropriate
- Unit tests in corresponding test file

### Every API endpoint MUST have:

- OpenAPI documentation
- Input validation
- Error handling
- Rate limiting considerations
- Security measures

### Every service MUST have:

- Health check endpoint
- Metrics endpoint
- Proper logging
- Graceful shutdown handling
- Docker support

## 🎯 CURRENT PROJECT STATUS

Based on analysis, we currently have:

- ✅ Root structure is mostly correct
- ✅ Service structure exists but needs reorganization
- ❌ Source code is mixed in with config files
- ❌ No proper separation of concerns
- ❌ Missing infrastructure layer
- ❌ No proper test organization

## 🔄 NEXT STEPS FOR RESTRUCTURING

1. **Reorganize src/ directory** according to layered architecture
2. **Move configuration files** to proper config/ directory
3. **Separate test files** from source code
4. **Create infrastructure/** directory for deployment configs
5. **Implement proper requirements** management
6. **Add missing documentation** structure

This structure will be **ALWAYS FOLLOWED** for any new files or modifications.
