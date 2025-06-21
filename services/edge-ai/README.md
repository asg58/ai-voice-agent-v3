# Edge AI Service

Edge AI Service voor het uitvoeren van AI-modellen op edge devices.

## Functionaliteit

- Verwerking van AI-modellen op edge devices
- Integratie met Service Discovery
- RESTful API met FastAPI
- Health checks en monitoring

## Architectuur

De service is gebouwd met FastAPI en volgt een modulaire structuur:

- `app/api/`: API endpoints
- `app/core/`: Core functionaliteit en configuratie
- `app/models/`: Data models
- `app/services/`: Service implementaties

## API Endpoints

- `GET /api/v1/health`: Health check endpoint
- `POST /api/v1/process`: Verwerk data met AI-modellen

## Lokale Ontwikkeling

1. Installeer de dependencies:

```bash
pip install -r requirements.txt
```

2. Start de service:

```bash
python run_local.py
```

De service is nu beschikbaar op `http://localhost:8500`.

## Docker

De service kan ook worden uitgevoerd met Docker:

```bash
docker build -t edge-ai .
docker run -p 8500:8500 edge-ai
```

## Integratie met Service Discovery

De service registreert zichzelf automatisch bij de Service Discovery service en stuurt regelmatig heartbeats om aan te geven dat de service nog actief is.

## Toekomstige Verbeteringen

- Implementatie van echte AI-modellen
- Model versioning en lifecycle management
- Model optimalisatie voor edge devices
- Batching voor efficiënte inferentie
- Integratie met model registry