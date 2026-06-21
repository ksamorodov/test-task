# Campaign Analytics

Client-server web app built with **Python / FastAPI** (backend) and **Angular 17 + Chart.js** (frontend).

## Project layout

```
test-task/
├── interview/              # source data CSVs
│   ├── interview.X.csv
│   └── interview.y.csv
├── backend/
│   ├── app/
│   │   ├── config.py       
│   │   ├── repository.py   # load DataFrame, lru_cache
│   │   ├── service.py      # calculate CTR / EvPM
│   │   ├── schemas.py      # API response schemas
│   │   ├── router.py       # FastAPI-router
│   │   └── main.py         
│   ├── tests/
│   │   ├── conftest.py     
│   │   ├── test_repository.py
│   │   ├── test_service.py
│   │   └── test_router.py
│   ├── pyproject.toml      
│   └── requirements.txt
└── frontend/               # Angular 17 + Chart.js
```

## Run (development)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
# API available at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npx ng serve
# App available at http://localhost:4200
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/event-types` | List all event tags |
| GET | `/api/timeseries?event=<tag>` | Daily CTR & EvPM |
| GET | `/api/aggregation?by=mm_dma\|site_id&event=<tag>` | Aggregated table |

## Tests

```bash
cd backend
source .venv/bin/activate 
pytest
```
