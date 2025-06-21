# 🎙️ AI Voice Agent v3

## Overzicht

AI Voice Agent v3 is een geavanceerd, realtime spraak-AI platform dat gebruikers in staat stelt om natuurlijke gesprekken te voeren met AI-assistenten. Het platform ondersteunt continue spraakherkenning, intelligente gespreksverwerking, en realtime antwoorden.

## 🚀 Hoofdfuncties

### 🎯 **Realtime Spraakverwerking**
- **Continue spraakherkenning** met WebRTC
- **Lage latency** processing (< 500ms)
- **Multi-language support** (Nederlands, Engels, meer)
- **Noise cancellation** en audio optimalisatie

### 🧠 **Intelligente AI Verwerking**
- **OpenAI GPT-4** integratie voor geavanceerde gesprekken
- **Context-aware** gespreksbeheer
- **Memory management** voor lange gesprekssessies
- **Sentiment analysis** en emotieherkenning

### 🏗️ **Microservices Architectuur**
- **Modulaire opzet** met loosely coupled services
- **Docker containerization** voor eenvoudige deployment
- **Service discovery** en load balancing
- **Health monitoring** en auto-recovery

### 💾 **Data & Storage**
- **PostgreSQL** voor gebruikersdata en gesprekgeschiedenis
- **Redis** voor caching en session management
- **Vector database** (Weaviate) voor AI embeddings
- **MinIO** object storage voor audio bestanden

## 🏛️ Architectuur

### Service Overzicht

```
AI Voice Agent v3
├── 🎙️ Voice Module (Port 8001)
├── 🧠 Core Engine (Port 8000)
├── 📄 Document Module (Port 8002)
├── 🌐 API Gateway (Port 8080)
├── 📊 Dashboard (Port 3000)
└── 🔍 Service Discovery & Mesh
```

### Technologie Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI + Python 3.11 | REST API services |
| **Database** | PostgreSQL 15 | Primary data storage |
| **Cache** | Redis 7 | Session & performance caching |
| **Vector DB** | Weaviate | AI embeddings & search |
| **Storage** | MinIO | Object storage (audio/docs) |
| **Containerization** | Docker + Docker Compose | Service orchestration |
| **Monitoring** | Prometheus + Grafana | Metrics & monitoring |
| **CI/CD** | GitHub Actions | Automated deployment |

## 🚀 Quick Start

### Prerequisites

- **Docker** en **Docker Compose** geïnstalleerd
- **Python 3.11+** voor lokale ontwikkeling
- **Node.js 18+** voor frontend development
- **Git** voor version control

### 1. Clone de Repository

```bash
git clone https://github.com/your-org/ai-voice-agent-v3.git
cd ai-voice-agent-v3
```

### 2. Environment Setup

```bash
# Kopieer environment template
cp .env.example .env

# Bewerk .env met jouw configuratie
nano .env
```

### 3. Start alle Services

```bash
# Start complete stack
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Verify Installation

```bash
# Check API Gateway
curl http://localhost:8080/health

# Check Core Engine
curl http://localhost:8000/health

# Check Voice Module
curl http://localhost:8001/health
```

### 5. Access Dashboard

Open je browser en ga naar:
- **Dashboard**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Grafana Monitoring**: http://localhost:3001

## 📁 Project Structuur

```
ai-voice-agent-v3/
├── 📁 services/                    # Microservices
│   ├── 📁 core-engine/            # Main AI processing
│   ├── 📁 voice-module/           # Voice processing
│   ├── 📁 document-module/        # Document processing
│   ├── 📁 api-gateway/            # API gateway
│   └── 📁 dashboard/              # Management dashboard
├── 📁 shared/                     # Shared utilities
│   ├── 📁 logging/               # Centralized logging
│   ├── 📁 config/                # Shared configuration
│   ├── 📁 models/                # Shared data models
│   └── 📁 utils/                 # Common utilities
├── 📁 infrastructure/             # Infrastructure as code
│   ├── 📁 docker/                # Docker configurations
│   ├── 📁 kubernetes/            # K8s manifests
│   └── 📁 monitoring/            # Monitoring configs
├── 📁 docs/                      # Documentation
├── 📁 tests/                     # Test suites
├── 📁 scripts/                   # Utility scripts
└── 📄 docker-compose.yml         # Main compose file
```

## 🔧 Development

### Lokale Development Setup

1. **Python Virtual Environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Database Setup**:
   ```bash
   # Start alleen database services
   docker-compose up -d postgres redis

   # Run database migrations
   cd services/core-engine
   alembic upgrade head
   ```

3. **Start Services Individueel**:
   ```bash
   # Core Engine
   cd services/core-engine
   python -m uvicorn app.main:app --reload --port 8000

   # Voice Module
   cd services/voice-module
   python -m uvicorn app.main:app --reload --port 8001
   ```

### Testing

```bash
# Run all tests
pytest

# Run specific service tests
pytest services/core-engine/tests/

# Run with coverage
pytest --cov=services --cov-report=html
```

### Code Quality

```bash
# Formatting
black services/
isort services/

# Linting
pylint services/
flake8 services/

# Type checking
mypy services/
```

## 📚 API Documentation

### Interactive API Docs

- **Core Engine**: http://localhost:8000/docs
- **Voice Module**: http://localhost:8001/docs
- **Document Module**: http://localhost:8002/docs
- **API Gateway**: http://localhost:8080/docs

### Key Endpoints

| Service | Endpoint | Description |
|---------|----------|-------------|
| API Gateway | `POST /api/v1/conversation` | Start gesprek |
| Voice Module | `POST /api/v1/voice/process` | Verwerk audio |
| Core Engine | `POST /api/v1/ai/process` | AI verwerking |
| Document Module | `POST /api/v1/documents/upload` | Upload document |

## 📊 Monitoring & Observability

### Health Checks

Alle services hebben health check endpoints:
- Core Engine: `GET /health`
- Voice Module: `GET /health`
- Document Module: `GET /health`
- API Gateway: `GET /health`

### Metrics

Prometheus metrics beschikbaar op:
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001

### Logging

Structured JSON logging naar stdout. Configuratie via environment variables:
```env
LOG_LEVEL=INFO
ENABLE_JSON_LOGGING=true
```

## 🚀 Deployment

### Production Deployment

1. **Environment Configuration**:
   ```bash
   cp .env.production .env
   # Update productie configuratie
   ```

2. **Build & Deploy**:
   ```bash
   docker-compose up -d
   ```

3. **Database Migrations**:
   ```bash
   docker-compose exec core-engine alembic upgrade head
   ```

## 🤝 Contributing

### Development Workflow

1. **Fork** het project
2. **Create** een feature branch (`git checkout -b feature/nieuwe-functie`)
3. **Commit** je wijzigingen (`git commit -am 'Voeg nieuwe functie toe'`)
4. **Push** naar de branch (`git push origin feature/nieuwe-functie`)
5. **Create** een Pull Request

### Code Standards

- Volg **PEP 8** Python coding standards
- Schrijf **comprehensive tests** voor nieuwe functies
- Update **documentatie** voor API wijzigingen
- Gebruik **conventional commits** voor commit messages

## 📄 License

Dit project valt onder de MIT License.

---

**Made with ❤️ by the AI Voice Agent Team**