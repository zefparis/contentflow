import logging
from sqlalchemy import create_engine
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Use DATABASE_URL from settings (uppercase field in Settings)
DATABASE_URL = getattr(settings, "DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL.lower() else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logger = logging.getLogger("contentflow.db")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """Create all tables based on models metadata."""
    # Import models to register metadata, then create all
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # --- lightweight auto-migrations for missing columns ---
    insp = sa.inspect(engine)

    def has_column(table: str, column: str) -> bool:
        try:
            cols = [c["name"] for c in insp.get_columns(table)]
            return column in cols
        except Exception:
            return False

    def add_column(table: str, column: str, type_sqlite: str, type_pg: str, default_sql: str | None = None):
        dialect = engine.dialect.name
        coltype = type_pg if dialect.startswith("post") else type_sqlite
        default_clause = f" DEFAULT {default_sql}" if default_sql else ""
        sql = f"ALTER TABLE {table} ADD COLUMN {column} {coltype}{default_clause}"
        with engine.begin() as conn:
            try:
                conn.execute(sa.text(sql))
            except Exception:
                pass

    # metric_events: ensure timestamp
    if insp.has_table("metric_events") and not has_column("metric_events", "timestamp"):
        add_column("metric_events", "timestamp", "DATETIME", "TIMESTAMP", "CURRENT_TIMESTAMP")

    # jobs: ensure all expected columns exist
    if insp.has_table("jobs"):
        # Ensure idempotency_key column exists
        if not has_column("jobs", "idempotency_key"):
            add_column("jobs", "idempotency_key", "VARCHAR(32)", "VARCHAR(32)")
            # Create unique index if it doesn't exist
            with engine.begin() as conn:
                try:
                    if engine.dialect.name.startswith('postgresql'):
                        conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_jobs_idempotency_key ON jobs (idempotency_key)"))
                    else:  # SQLite
                        conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_jobs_idempotency_key ON jobs (idempotency_key)"))
                except Exception as e:
                    logger.warning(f"Could not create idempotency_key index: {e}")
        
        # Ensure other required columns exist
        if not has_column("jobs", "payload"):
            # JSONB on Postgres, TEXT on SQLite
            add_column("jobs", "payload", "TEXT", "JSONB")
        if not has_column("jobs", "attempts"):
            add_column("jobs", "attempts", "INTEGER", "INTEGER", "0")
        if not has_column("jobs", "status"):
            add_column("jobs", "status", "TEXT", "TEXT", "'queued'")
        # DLQ reason text column for failure diagnostics
        if not has_column("jobs", "dlq_reason"):
            add_column("jobs", "dlq_reason", "TEXT", "TEXT")
        for ts_col in ("created_at", "started_at", "completed_at"):
            if not has_column("jobs", ts_col):
                add_column("jobs", ts_col, "DATETIME", "TIMESTAMP", 
                          "CURRENT_TIMESTAMP" if ts_col == "created_at" else None)

# Backward-compat alias for older routes expecting get_session
get_session = get_db
