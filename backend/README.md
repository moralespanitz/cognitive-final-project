# TaxiWatch Backend - FastAPI + Lambda

## Tech Stack
- FastAPI 0.104+
- SQLAlchemy 2.0 (async)
- PostgreSQL
- SQLAdmin
- AWS Lambda (via Mangum)
- OpenAI API

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start development server:
```bash
uvicorn app.main:app --reload
```

5. Access:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Admin: http://localhost:8000/admin

### Database Migrations

Create new migration:
```bash
alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback:
```bash
alembic downgrade -1
```

### Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

## Project Structure

```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   ├── core/            # Core utilities
│   ├── admin/           # SQLAdmin setup
│   ├── lambda_handlers/ # AWS Lambda handlers
│   ├── config.py        # Settings
│   ├── database.py      # DB setup
│   └── main.py          # FastAPI app
├── alembic/             # DB migrations
├── tests/               # Tests
└── requirements.txt     # Dependencies
```

## AWS Lambda Deployment

See `../terraform/` for infrastructure setup.

Build Lambda package:
```bash
../scripts/build_lambda.sh
```

Deploy:
```bash
cd ../terraform
terraform apply
```
