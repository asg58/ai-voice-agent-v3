# Common Module

Deze module bevat gemeenschappelijke code die wordt gedeeld tussen alle services in het AI Voice Agent platform.

## Overzicht

De common module biedt herbruikbare componenten voor:

- FastAPI applicatie configuratie
- Logging
- Middleware
- Health checks
- Metrics
- Utilities

## Installatie

Installeer de module in development mode:

```bash
pip install -e services/common
```

Of voeg het toe aan je requirements.txt:

```
-e ../common
```

## Gebruik

### App Factory

De app factory maakt het gemakkelijk om een gestandaardiseerde FastAPI applicatie te maken:

```python
from common.app.base.app_factory import create_app
from common.app.base.logging import configure_logging
from app.core.config import settings

# Configure logging
logger = configure_logging(
    service_name="my-service",
    log_level=settings.LOG_LEVEL
)

# Create FastAPI application
app = create_app(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan_handler=lifespan_handler,
    cors_origins=settings.CORS_ORIGINS,
    enable_metrics=settings.ENABLE_METRICS
)
```

### Health Checks

Maak gestandaardiseerde health check endpoints:

```python
from datetime import datetime
from fastapi import APIRouter

from common.app.base.health import create_health_router
from ..core.config import settings

# Create health router
router = create_health_router(
    service_name=settings.APP_NAME,
    version=settings.APP_VERSION,
    start_time=datetime.now()
)

# Add custom endpoints
@router.get("/custom-health", summary="Custom health check")
async def custom_health():
    return {"status": "healthy", "custom": True}
```

### Logging

Configureer logging voor je service:

```python
from common.app.base.logging import configure_logging

logger = configure_logging(
    service_name="my-service",
    log_level="INFO"
)

logger.info("Application started")
logger.error("An error occurred", exc_info=True)
```

### Metrics

Gebruik de metrics middleware voor Prometheus metrics:

```python
from common.app.base.metrics import setup_metrics

# In your app factory or main.py
metrics = setup_metrics(app)
```

## Componenten

### app/base/app_factory.py

Factory functie voor het maken van FastAPI applicaties met gestandaardiseerde configuratie.

### app/base/logging.py

Configuratie voor gestandaardiseerde logging.

### app/base/middleware.py

Gemeenschappelijke middleware voor alle services.

### app/base/metrics.py

Prometheus metrics configuratie.

### app/base/health.py

Gestandaardiseerde health check endpoints.

### app/utils/

Diverse utility functies voor alle services.

## Ontwikkeling

### Nieuwe componenten toevoegen

1. Voeg nieuwe componenten toe in de juiste map
2. Voeg tests toe in de tests map
3. Update de documentatie
4. Voeg de component toe aan de `__init__.py` van de betreffende map

### Tests uitvoeren

```bash
cd services/common
pytest
```
