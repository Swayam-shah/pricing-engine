"""
FastAPI app entry point.
Run with: uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from api.routes import router

# ── Create FastAPI app ────────────────────────────────────────────────────────
app = FastAPI(
    title="Pricing Engine API",
    description="Autonomous competitor price tracking and AI pricing recommendations",
    version="1.0.0"
)

# ── CORS — allows Next.js frontend to call this API ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routes under /api prefix ─────────────────────────────────────
app.include_router(router, prefix="/api")


# ── Startup event — create DB tables if they don't exist ─────────────────────
@app.on_event("startup")
async def startup():
    init_db()
    print("🚀 Pricing Engine API started")
    print("📖 Docs available at: http://localhost:8000/docs")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Pricing Engine API",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}