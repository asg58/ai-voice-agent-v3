# Service Mesh

Service Mesh voor het beheren van communicatie tussen microservices in het AI Voice Agent platform.

## Functionaliteit

- Service discovery integratie
- Load balancing en request routing
- Circuit breaking voor foutafhandeling
- Rate limiting voor traffic management
- Distributed tracing en metrics collection
- Configuratie via YAML-bestanden

## Architectuur

De service bestaat uit verschillende componenten:

- **Router**: Verantwoordelijk voor het routeren van requests naar services
- **Circuit Breaker**: Voorkomt cascading failures door services tijdelijk uit te schakelen
- **Rate Limiter**: Beperkt het aantal requests naar services
- **Telemetry**: Verzamelt metrics en tracing informatie
- **Config Loader**: Laadt configuratie uit YAML-bestanden

## API Endpoints

- `GET /api/v1/health`: Health check endpoint
- `POST /api/v1/proxy`: Proxy een request naar een service
- `POST /api/v1/proxy/{service_name}/{path}`: Proxy een request naar een specifieke service en pad
- `GET /api/v1/config`: Haal de mesh configuratie op
- `GET /api/v1/config/services`: Haal alle service configuraties op
- `GET /api/v1/config/services/{service_name}`: Haal een specifieke service configuratie op
- `GET /api/v1/config/routes`: Haal alle routes op
- `GET /api/v1/telemetry/spans`: Haal alle spans op
- `GET /api/v1/telemetry/metrics`: Haal alle metrics op
- `GET /api/v1/telemetry/logs`: Haal alle logs op
- `GET /api/v1/telemetry/circuit-breakers`: Haal de status van alle circuit breakers op
- `GET /api/v1/telemetry/rate-limiters`: Haal de status van alle rate limiters op

## Configuratie

De service wordt geconfigureerd via een YAML-bestand. Hier is een voorbeeld:

```yaml
services:
  - name: api-gateway
    circuit_breaker:
      enabled: true
      threshold: 5
      timeout: 30
    rate_limit:
      enabled: true
      requests: 100
      window: 60
    routes:
      - name: api-gateway-route
        match:
          path: /api
          method: GET
        destinations:
          - service_name: api-gateway
            weight: 100
```

## Lokale Ontwikkeling

1. Installeer de dependencies:

```bash
pip install -r requirements.txt
```

2. Start de service:

```bash
uvicorn app.main:app --reload --port 8600
```

De service is nu beschikbaar op `http://localhost:8600`.

## Docker

De service kan ook worden uitgevoerd met Docker:

```bash
docker build -t service-mesh .
docker run -p 8600:8600 service-mesh
```