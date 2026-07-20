# Personal Expense Tracker

A full-stack expense tracking application with JWT authentication, built for Nolyth Sprint 01 — Backend Foundations. The system exposes a REST API for managing users, categories, and expenses, backed by a relational database, with a Streamlit client consuming that API.

Live demo: https://knightrehman-personal-expense-trac-frontendstreamlit-app-huoymm.streamlit.app/
API documentation: https://personal-expense-tracker-nolyth-spr-xi.vercel.app/docs

## Overview

The application allows a user to register an account, authenticate via JWT, define spending categories, and record expenses against those categories. All data is scoped per user — no user can read, modify, or delete another user's records, even by guessing an object ID. The API is fully documented via OpenAPI/Swagger and validated end to end with Pydantic schemas.

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Language | Python 3.12 |
| ORM | SQLAlchemy 2.x |
| Database | SQLite (local development), PostgreSQL (production) |
| Authentication | JSON Web Tokens (python-jose), bcrypt password hashing (passlib) |
| Validation | Pydantic v2 |
| Frontend | Streamlit |
| Deployment | Vercel (API), Neon (PostgreSQL), Streamlit Community Cloud (UI) |

## Architecture

expense-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py          Application entrypoint: app instance, CORS, exception handlers, router registration
│   │   ├── database.py      Engine and session configuration; resolves DATABASE_URL for SQLite or PostgreSQL
│   │   ├── models.py        SQLAlchemy models: User, Category, Expense, and their relationships
│   │   ├── schemas.py       Pydantic request and response models
│   │   ├── auth.py          Password hashing, JWT issuance and verification, current-user dependency
│   │   ├── crud.py          Database query functions consumed by the routers
│   │   └── routers/
│   │       ├── auth.py        Registration, login, current user
│   │       ├── categories.py  Category CRUD
│   │       └── expenses.py    Expense CRUD and summary aggregation
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py     Streamlit client; communicates with the API exclusively over HTTP
│   └── requirements.txt
├── screenshots/
└── README.md

The frontend holds no business logic or direct database access. Every action in the UI corresponds to a call against the documented API surface.

## Data Model

User (1) ──── (many) Category
User (1) ──── (many) Expense
Category (1) ── (many) Expense

Every category and expense record carries a `user_id` foreign key, and every query in `crud.py` filters on it. Authorization is therefore enforced at the query layer, not only at the route layer.

## API Reference

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/` | No | Health check |
| POST | `/auth/register` | No | Create a new user account |
| POST | `/auth/login` | No | Authenticate and receive a JWT access token |
| GET | `/auth/me` | Yes | Return the authenticated user's profile |
| POST | `/categories/` | Yes | Create a category |
| GET | `/categories/` | Yes | List categories owned by the authenticated user |
| DELETE | `/categories/{id}` | Yes | Delete a category; rejected if expenses still reference it |
| POST | `/expenses/` | Yes | Create an expense |
| GET | `/expenses/` | Yes | List expenses, with optional `category_id`, `start_date`, `end_date` filters |
| GET | `/expenses/summary` | Yes | Total spend and per-category aggregation |
| GET | `/expenses/{id}` | Yes | Retrieve a single expense |
| PUT | `/expenses/{id}` | Yes | Update an expense (partial updates supported) |
| DELETE | `/expenses/{id}` | Yes | Delete an expense |

Interactive documentation with request/response schemas and a try-it-out interface is generated automatically at `/docs` (Swagger UI) and `/redoc` (ReDoc) once the backend is running.

## Error Handling

Validation errors return HTTP 422 with a structured payload identifying the offending field and reason. Authentication failures return 401. Ownership or not-found violations return 404. Business-rule violations, such as deleting a category with existing expenses, return 400 with a descriptive message. A custom exception handler in `main.py` normalizes FastAPI's default validation error format into a more consumable shape for API clients.

## Local Setup

### Prerequisites

- Python 3.10 or later
- pip

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API starts at `http://127.0.0.1:8000`. On first run, a local SQLite database file (`expenses.db`) is created automatically; no manual schema setup is required.

Environment variables (optional for local development):

```bash
SECRET_KEY=<a long random string>                          # JWT signing key
DATABASE_URL=postgresql://user:password@host:5432/dbname    # overrides the SQLite default
```

### Frontend

With the backend running, in a separate terminal:

```bash
cd frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The UI starts at `http://localhost:8501`. Set `API_URL` if the backend is not running at the default local address:

```bash
API_URL=http://127.0.0.1:8000 streamlit run streamlit_app.py
```

## Deployment

| Component | Platform | Notes |
|---|---|---|
| Database | Neon | Managed PostgreSQL; connection string set as `DATABASE_URL` on the API host |
| API | Vercel | Serverless Python functions; entrypoint at `backend/main.py`, re-exporting the FastAPI instance from `app/main.py` |
| Frontend | Streamlit Community Cloud | Main file `frontend/streamlit_app.py`; `API_URL` set via Streamlit secrets |

`database.py` normalizes the `postgres://` scheme some providers issue into the `postgresql://` scheme SQLAlchemy 2.x requires, and explicitly routes connections through the `psycopg` (v3) driver rather than the default `psycopg2`, since `psycopg2`'s compiled extension does not reliably import in Vercel's serverless Python runtime. No code change is needed when moving from local SQLite to hosted Postgres beyond setting `DATABASE_URL`.

Table creation on startup (`Base.metadata.create_all`) is wrapped in a try/except so a transient database connection issue fails loudly in the logs rather than taking down the entire API, including `/docs`.

## Design Notes

- Pydantic schemas (`schemas.py`) are kept separate from SQLAlchemy models (`models.py`) so that internal fields, such as the hashed password, are never serializable into an API response, and so that input validation rules are independent of database column definitions.
- Query logic is isolated in `crud.py` rather than inlined in route handlers, keeping routers focused on HTTP concerns (status codes, dependency injection, authorization) while queries remain independently reusable and testable.
- Authentication is stateless via JWT rather than server-side sessions, which keeps the API usable by any client — the Streamlit frontend here, but equally a single-page application or mobile client without modification.
- Ownership checks are applied uniformly at the query layer: every lookup by ID is filtered by the authenticated user's `user_id`, preventing access to another user's records regardless of route-level checks.

## Testing

The API has been exercised end to end using FastAPI's `TestClient`, covering registration, duplicate-user rejection, login and invalid-credential handling, unauthorized access, category and expense CRUD, input validation failures, ownership boundaries, and the summary aggregation. Manual verification checklist:

1. Register a user and log in.
2. Create a category; attempt to create a duplicate and confirm rejection.
3. Create expenses against the category; attempt a non-positive amount and confirm rejection.
4. Filter expenses by category and by date range.
5. Confirm the summary endpoint reflects the correct totals.
6. Attempt to delete a category with existing expenses and confirm rejection.
7. Delete an expense and confirm it no longer appears in listings or the summary.

## Author

Wasi-Ur-Rehman
Nolyth Sprint 01 — Backend Foundations