from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.routers import dashboard, chat, ai_context

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(ai_context.router, prefix="/api/dashboard", tags=["ai"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Backend Keday70 API is running!", "db": "SQLite"}

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