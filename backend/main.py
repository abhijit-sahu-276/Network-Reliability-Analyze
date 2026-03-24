from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.routes.ai_routes import router as ai_router
from backend.routes.network import router as network_router
from backend.services.repository import init_db, recent_analyses


app = FastAPI(
    title="AI-Powered Network Reliability Analyzer API",
    version="1.0.0",
    description="Full-stack backend for reliability analysis, failure simulation, and AI-assisted optimization.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(network_router)
app.include_router(ai_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root():
    return {
        "service": "AI-Powered Network Reliability Analyzer API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/history")
def history(limit: int = 20):
    limit = max(1, min(limit, 200))
    return {"items": recent_analyses(limit)}


frontend_dist = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dist.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


@app.exception_handler(ValueError)
def value_error_handler(_, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})
