"""
   Vercel entrypoint.

   Vercel's Python runtime auto-detects a FastAPI/ASGI app from a top-level
   main.py (no pyproject.toml or vercel.json needed). The real application
   lives in app/main.py; this file just re-exports it so Vercel can find it
   at the location it expects.
   """
   from app.main import app