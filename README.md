# Personal Expense Tracker

A full-stack expense tracking application built for **Nolyth Sprint 01 — Backend Foundations**.
Users register, log in, create spending categories, and log expenses against them through a
Streamlit UI backed by a FastAPI + SQLAlchemy REST API with JWT authentication.

> Built and tested end-to-end. All endpoints below were exercised with an automated smoke test
> before this repo was finalized (register → login → protected CRUD → validation errors →
> ownership checks → delete → summary).

## Why this project (mapped to sprint requirements)

| Sprint requirement | Where it lives |
|---|---|
| Authentication / protected user action | JWT login (`/auth/login`) protects every category & expense route |
| 4+ meaningful CRUD/API endpoints | 11 endpoints across auth, categories, expenses (see table below) |
| Pydantic request/response validation | `app/schemas.py` — e.g. `amount` must be `> 0`, usernames have length limits |
| Database models + persistent storage | `app/models.py` — SQLAlchemy models with real relationships (User → Category → Expense) |
| Error handling with helpful messages | Custom 400/401/404/422 responses with human-readable `detail` text |
| Streamlit UI calling the API | `frontend/streamlit_app.py` — forms, tables, buttons, filters, a bar chart |
| GitHub repo with README + setup | This file |
| Demo | See "Demo Script" section below |

## Tech Stack

- **Python 3.12**
- **FastAPI** — REST API, routing, auto-generated docs (`/docs`, `/redoc`)
- **SQLAlchemy** — ORM models, relationships, session management
- **SQLite** (default, zero setup) — swappable to PostgreSQL via `DATABASE_URL`
- **Pydantic v2** — request/response schemas and validation
- **python-jose + passlib[bcrypt]** — JWT issuing/verification and password hashing
- **Streamlit** — frontend UI
- **requests / pandas** — API client and table rendering in the UI

## Architecture

```
expense-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app, CORS, exception handlers, router registration
│   │   ├── database.py      # Engine/session setup (SQLite by default)
│   │   ├── models.py        # SQLAlchemy models: User, Category, Expense
│   │   ├── schemas.py       # Pydantic request/response models
│   │   ├── auth.py          # Password hashing, JWT create/verify, get_current_user dependency
│   │   ├── crud.py          # DB query functions used by routers
│   │   └── routers/
│   │       ├── auth.py        # /auth/register, /auth/login, /auth/me
│   │       ├── categories.py  # /categories CRUD
│   │       └── expenses.py    # /expenses CRUD + /expenses/summary
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py     # Streamlit UI — pure API client, no DB access
│   └── requirements.txt
├── screenshots/             # Add your screenshots here (see below)
└── README.md
```

**Data model:**

```
User 1───* Category 1───* Expense
User 1─────────────────* Expense   (every expense also links straight back to its owner)
```

Each user only ever sees their own categories and expenses — every query is filtered by
`user_id`, and the current user is resolved from the JWT on every protected request.

## API Endpoints

| Method | Path | Auth required | Description |
|---|---|---|---|
| GET | `/` | No | Health check |
| POST | `/auth/register` | No | Create a new user account |
| POST | `/auth/login` | No | Log in, returns a JWT access token |
| GET | `/auth/me` | Yes | Get the logged-in user's profile |
| POST | `/categories/` | Yes | Create a category |
| GET | `/categories/` | Yes | List your categories |
| DELETE | `/categories/{id}` | Yes | Delete a category (blocked if expenses reference it) |
| POST | `/expenses/` | Yes | Create an expense |
| GET | `/expenses/` | Yes | List expenses (optional `category_id`, `start_date`, `end_date` filters) |
| GET | `/expenses/summary` | Yes | Total spend + per-category breakdown |
| GET | `/expenses/{id}` | Yes | Get a single expense |
| PUT | `/expenses/{id}` | Yes | Update an expense (partial updates supported) |
| DELETE | `/expenses/{id}` | Yes | Delete an expense |

Full interactive documentation (try-it-out included) is auto-generated at `/docs` once the
backend is running.

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API is now running at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` for
Swagger UI. A `expenses.db` SQLite file is created automatically on first run — no manual
database setup needed.

**Optional environment variables:**

```bash
export SECRET_KEY="something-long-and-random"      # JWT signing key (set this in production)
export DATABASE_URL="postgresql://user:pass@localhost:5432/expenses"  # switch to Postgres
```

### 2. Frontend

In a **second terminal** (keep the backend running):

```bash
cd frontend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit opens at `http://localhost:8501`. If your backend runs somewhere other than
`http://127.0.0.1:8000`, set `API_URL` before launching:

```bash
export API_URL="http://127.0.0.1:8000"
streamlit run streamlit_app.py
```

### 3. Try it

1. Register a user in the sidebar, then log in.
2. Go to the **Categories** tab and add a category (e.g. "Food", "Transport").
3. Go to the **Expenses** tab, add a few expenses against those categories.
4. Check the **Summary** tab for the total spend and per-category bar chart.

## Screenshots

Add screenshots of your running app here before submission:

- `screenshots/swagger-docs.png` — the `/docs` page showing all endpoints
- `screenshots/login.png` — the Streamlit login/register screen
- `screenshots/expenses-tab.png` — the expenses form + table
- `screenshots/summary-tab.png` — the summary tab with the bar chart

## Demo Script (for the review)

**Problem:** People lose track of day-to-day spending because it's scattered across receipts,
bank apps, and memory. This app gives a single place to log an expense in seconds and see
where money is actually going, broken down by category.

**Flow to walk through live:**
1. Register/login → show the JWT being issued and that `/expenses` returns 401 without it.
2. Create a category, then an expense → point out Pydantic rejecting a negative amount.
3. Show the API docs at `/docs` — routes, schemas, status codes, all auto-generated.
4. Show the database file / a quick `sqlite3 expenses.db "select * from expenses;"` to prove
   it's persisted, not hardcoded.
5. Switch to Streamlit → add/delete an expense, filter by category, show the summary chart
   updating live.

**Technical choices to be ready to explain:**
- Why JWT over session cookies: stateless, easy to plug into any frontend (Streamlit here,
  but the same API works with a JS SPA or mobile app unchanged).
- Why separate `schemas.py` (Pydantic) from `models.py` (SQLAlchemy): input validation and
  DB structure are different concerns — this also stops `hashed_password` from ever being
  serialized back to a client.
- Why `crud.py` is separate from the routers: keeps route handlers focused on HTTP concerns
  (status codes, auth) while query logic stays testable on its own.
- Ownership checks: every category/expense query is filtered by `user_id`, so one user can
  never read, edit, or delete another user's data even by guessing an ID.

## Notes

- SQLite is used by default for zero-setup grading; swapping to PostgreSQL is a one-line
  `DATABASE_URL` change since all access goes through SQLAlchemy.
- `SECRET_KEY` has a dev default so the project runs out of the box — set a real one via
  environment variable for anything beyond local grading/demo use.
