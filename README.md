# Campaign Analytics

Client-server web app built with **Python / FastAPI** (backend) and **Angular 17 + Chart.js** (frontend).

## Project layout

```
test-task/
├── interview/          # source data CSVs
│   ├── interview.X.csv
│   └── interview.y.csv
├── backend/
│   ├── main.py
│   └── requirements.txt
└── frontend/           # Angular project
```

## Run (development)

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
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
source .venv/bin/activate   # активировать venv (если ещё не активирован)
pytest test_main.py -v --cov=main --cov-report=term-missing
```

34 теста, ~1 сек. Реальные CSV не нужны — данные замоканы.

## Metrics

- **CTR** = events / impressions × 100 (%)
- **EvPM** = events / impressions × 1000 (events per thousand impressions)