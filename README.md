# CP Analyzer — backend skeleton

This repository contains a production-ready skeleton for a Competitive Programming Analyzer backend.

Tech highlights:
- FastAPI (async)
- Async SQLAlchemy 2.0
- PostgreSQL + Redis (Docker)
- Celery for background jobs
- Poetry for dependency management
- Alembic scaffold for migrations

Quick start (Docker):
1. Copy `.env.example` → `.env` and edit if needed.
2. docker compose up --build
3. Open http://localhost:8000/ and GET `/health`

Project layout: `app/` follows layered architecture: routers → services → repositories → models
