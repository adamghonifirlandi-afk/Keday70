from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
from backend.config.settings import ALLOWED_ORIGINS, ENVIRONMENT

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup: sync Excel → SQLite ──
    from backend.core.sync_excel_to_sqlite import sync
    sync()
    yield
    # ── Shutdown (cleanup jika perlu) ──

app = FastAPI(
    title="Keday70 Dashboard API",
    version="2.0.0",
    lifespan=lifespan,
)

# Parse ALLOWED_ORIGINS
if ALLOWED_ORIGINS == "*":
    origins = ["*"]
else:
    origins = [o.strip() for o in ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if ENVIRONMENT == "production":
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Terjadi kesalahan pada server. Silakan coba lagi nanti."},
        )

from backend.routers import dashboard, chat, ai_context

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ai_context.router, prefix="/api/dashboard", tags=["ai"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend Keday70 API is running!", "db": "SQLite"}

@app.get("/health")
def health_check():
    return {"status": "ok", "environment": ENVIRONMENT}

@app.post("/api/reload")
def reload_data():
    """Re-sync Excel → SQLite dan reload cache."""
    from backend.core.sync_excel_to_sqlite import sync
    from backend.core.loader import reload_data as _reload
    sync()
    _reload()
    return {"status": "ok", "message": "Data berhasil di-reload dari Excel ke SQLite."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)