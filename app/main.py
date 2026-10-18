"""FastAPI entrypoint. Readiness never writes to the database."""
from fastapi import FastAPI
from app.kanban.api import router

app = FastAPI(title="Assignment 7 Kanban API", version="1.0.0")
app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    """Process health only, NOT a database connectivity claim."""
    return {"status": "ok", "database": "not_checked"}
