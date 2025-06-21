# Dashboard Service

Dashboard Service voor het monitoren en beheren van het AI Voice Agent platform.

## Functionaliteit

- Monitoring van services en systeem metrics
- Beheer van alerts en notificaties
- Authenticatie en autorisatie met JWT
- Responsive UI met Material-UI

## Architectuur

De service bestaat uit twee delen:

### Backend (FastAPI)

- `app/api/`: API endpoints
- `app/core/`: Core functionaliteit en configuratie
- `app/models/`: Data models
- `app/routers/`: API routers
- `app/services/`: Service implementaties

### Frontend (React)

- `frontend/src/components/`: Herbruikbare UI componenten
- `frontend/src/pages/`: Pagina componenten
- `frontend/src/services/`: API services
- `frontend/src/context/`: React context providers
- `frontend/src/utils/`: Utility functies

## API Endpoints

- `GET /api/v1/health`: Health check endpoint
- `POST /api/v1/auth/login`: Login endpoint
- `GET /api/v1/auth/me`: Huidige gebruiker ophalen
- `GET /api/v1/dashboard/summary`: Dashboard samenvatting ophalen
- `GET /api/v1/dashboard/services`: Services ophalen
- `GET /api/v1/dashboard/metrics/system`: Systeem metrics ophalen
- `GET /api/v1/dashboard/alerts`: Alerts ophalen

## Lokale Ontwikkeling

### Backend

1. Installeer de dependencies:

```bash
pip install -r requirements.txt
```

2. Start de service:

```bash
uvicorn app.main:app --reload --port 8300
```

De backend is nu beschikbaar op `http://localhost:8300`.

### Frontend

1. Ga naar de frontend directory:

```bash
cd frontend
```

2. Installeer de dependencies:

```bash
npm install
```

3. Start de development server:

```bash
npm start
```

De frontend is nu beschikbaar op `http://localhost:3000`.

## Docker

De service kan ook worden uitgevoerd met Docker:

```bash
docker build -t dashboard .
docker run -p 8300:8300 dashboard
```

## Demo Accounts

- Admin: `admin` / `admin`
- User: `user` / `user`
- Viewer: `viewer` / `viewer`