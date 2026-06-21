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
│   │   ├── config.py       # pydantic-settings (пути к CSV, env APP_X_CSV / APP_Y_CSV)
│   │   ├── repository.py   # загрузка DataFrame, lru_cache
│   │   ├── service.py      # расчёт CTR / EvPM
│   │   ├── schemas.py      # Pydantic-модели ответов
│   │   ├── router.py       # FastAPI-роутер
│   │   └── main.py         # создание app, CORS, подключение роутера
│   ├── tests/
│   │   ├── conftest.py     # синтетические фикстуры, autouse-патч репозитория
│   │   ├── test_repository.py
│   │   ├── test_service.py
│   │   └── test_router.py
│   ├── pyproject.toml      # конфиг pytest + coverage
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
source .venv/bin/activate   # если venv ещё не активирован
pytest
```

42 теста, ~0.2 сек. Реальные CSV не нужны — репозиторий замокан синтетическими данными.

## Metrics

- **CTR** = events / impressions × 100 (%)
- **EvPM** = events / impressions × 1000 (events per thousand impressions)