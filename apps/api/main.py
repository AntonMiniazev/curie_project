# Use command `uvicorn main:app --reload` to run the server
from fastapi import FastAPI
from .routers import health, meta, reports, cache

app = FastAPI()

app.include_router(health.router)
app.include_router(meta.router)
app.include_router(reports.router)
app.include_router(cache.router)
