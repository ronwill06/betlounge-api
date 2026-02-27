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

### Deploy to Fly.io
1) Install and auth Fly CLI
```
brew install flyctl
fly auth login
```

2) Create app (first time only)
```
fly launch --no-deploy
```
Use app name `betlounge-api` (or update `fly.toml` with your chosen name).

3) Provision Postgres (if you do not already have one)
```
fly postgres create --name betlounge-db
fly postgres attach --app betlounge-api betlounge-db
```
This sets `DATABASE_URL` for your app.

4) If needed, set `DATABASE_URL` manually
```
fly secrets set DATABASE_URL='postgresql+psycopg2://USER:PASS@HOST:5432/DBNAME'
```

5) Deploy
```
fly deploy
```
Migrations run automatically during deploy via Fly release command (`alembic upgrade head`).

6) Optional: seed sample data
```
fly ssh console -C "python -c \"from app.db import SessionLocal; from app.seed import seed; db=SessionLocal(); seed(db); db.close()\""
```

7) Check health
```
fly status
fly logs
curl https://<your-app-name>.fly.dev/health
```
