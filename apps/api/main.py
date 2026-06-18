# Use command `uvicorn api.main:app --reload` to run the server
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .routers import health, meta, reports, cache, auth

app = FastAPI()
settings = get_settings()

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router)
app.include_router(meta.router)
app.include_router(reports.router)
app.include_router(cache.router)
app.include_router(auth.router)
