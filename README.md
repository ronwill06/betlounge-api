## BetLounge API (MVP)

### Quickstart
1) Start Postgres
```
docker compose up -d
```

2) Create `.env`
```
cat > .env << 'EOF'
DATABASE_URL=postgresql+psycopg2://betlounge:betlounge@localhost:5432/betlounge
EOF
```

3) Create and activate a virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```

4) Install dependencies
```
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e .
```

5) Run migrations (optional if no migrations yet)
```
alembic upgrade head
```

6) Seed sample data
```
python -c "from app.db import SessionLocal; from app.seed import seed; db=SessionLocal(); seed(db); db.close()"
```

7) Run the API
```
uvicorn app.main:app --reload
```

### Test endpoints
- http://localhost:8000/health
- http://localhost:8000/v1/props/top?sport=NBA&market=PRA&limit=10
- http://localhost:8000/v1/props/markets?sport=NBA
- http://localhost:8000/v1/props/search?query=LeB
