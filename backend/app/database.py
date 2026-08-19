import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_extensions(db=None):
    """Enable pgvector + embedding columns when available. Safe to run always."""
    try:
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text(
                "ALTER TABLE jobs ADD COLUMN IF NOT EXISTS embedding vector(1536)"
            ))
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_embedding vector(1536)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_jobs_embedding ON jobs USING ivfflat (embedding vector_cosine_ops)"
            ))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_users_embedding ON users USING ivfflat (profile_embedding vector_cosine_ops)"
            ))
        return True
    except Exception:
        logger.warning("pgvector not available, falling back to Python semantic search")
        return False


def is_pgvector_ready() -> bool:
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT 1 FROM pg_extension WHERE extname='vector'")
            ).fetchone()
            if not row:
                return False
            cols = {
                r[0]
                for r in conn.execute(text(
                    "SELECT column_name FROM information_schema.columns WHERE table_name='users'"
                ))
            }
            return "profile_embedding" in cols
    except Exception:
        return False


def init_db() -> None:
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    ensure_extensions()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
