"""Backward-compatible entrypoint.

Use ``uvicorn app.main:app`` in production. Existing local commands that import
``server:app`` continue to work during migration.
"""

from app.main import app as app

if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
