# AI Job Intelligence Backend Sandbox

14-day advanced Python backend practice project.

The goal is not to build a polished product immediately. The goal is to create a small backend sandbox where each day practices one production-style backend concept: clean architecture, external API adapters, PostgreSQL, migrations, deduplication, auth, AI provider abstraction, workers, reliability, tests, and system design.

## Day 1 scope

Day 1 initializes the backend skeleton:

- FastAPI app entry point
- API router structure
- settings layer
- `/health` endpoint
- health endpoint test
- empty folders for future backend layers

## Project structure

```text
app/
  main.py
  api/
    v1/
      router.py
      endpoints/
        health.py
  core/
    config.py
  db/
  models/
  schemas/
  services/
  repositories/
  integrations/
tests/
  test_health.py
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Verification

Compile app files:

```bash
python -m py_compile $(find app -name "*.py")
```

Run API:

```bash
uvicorn app.main:app --reload
```

Smoke test:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "AI Job Intelligence Backend",
  "environment": "local"
}
```

Run tests:

```bash
pytest -q
```

## Day 1 interview note

This project starts with clear backend boundaries. Routes handle HTTP concerns, services will hold business logic, repositories will handle database access, integrations will isolate external APIs and AI providers, and schemas will define API contracts. Even though Day 1 only exposes `/health`, the structure prepares the project for clean growth across the 14-day challenge.
