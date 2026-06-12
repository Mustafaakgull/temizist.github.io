from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import text
from database.database import engine, Base
from routers import mobile_api, pi_api


async def _migrate_session_columns(conn):
    """PostgreSQL: sessions tablosuna yeni kolonlar (varsa atlanır)."""
    stmts = (
        "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS waste_type VARCHAR DEFAULT 'plastic'",
        "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS plastic_bottle_count INTEGER DEFAULT 0",
        "ALTER TABLE sessions ADD COLUMN IF NOT EXISTS paper_count INTEGER DEFAULT 0",
    )
    for stmt in stmts:
        await conn.execute(text(stmt))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_session_columns(conn)
    yield
    # Cleanup on shutdown if needed
    pass

app = FastAPI(
    title="TemizIST API",
    debug=True,
    description="Backend API for TemizIST Smart Recycling System",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(mobile_api.router)
app.include_router(pi_api.router)

@app.get("/")
async def root():
    return {"message": "Welcome to TemizIST API"}
