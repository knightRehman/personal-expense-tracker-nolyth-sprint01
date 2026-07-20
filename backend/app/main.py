"""
Personal Expense Tracker API — Nolyth Sprint 01 project.

Run locally:
    uvicorn app.main:app --reload
"""
from app.database import Base, engine
from app.routers import auth, categories, expenses

import sys
try:
    Base.metadata.create_all(bind=engine)
except Exception as _startup_db_error:
    print(f"[STARTUP WARNING] Could not create database tables: {_startup_db_error!r}", file=sys.stderr)

app = FastAPI(
    title="Personal Expense Tracker API",
    description=(
        "A backend for tracking personal expenses by category, built for "
        "Nolyth Sprint 01: Backend Foundations. Includes JWT authentication, "
        "SQLAlchemy models with relationships, and full CRUD."
    ),
    version="1.0.0",
)

# Allow the Streamlit frontend (or any local client) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(expenses.router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Turn Pydantic's default validation error payload into something
    friendlier for API consumers (e.g. the Streamlit UI) to display."""
    errors = [
        {"field": ".".join(str(loc) for loc in err["loc"] if loc != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed.", "errors": errors},
    )


@app.get("/", tags=["Health"], summary="Health check")
def root():
    return {"status": "ok", "message": "Expense Tracker API is running. Visit /docs for API documentation."}
