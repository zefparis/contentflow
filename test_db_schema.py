import asyncio
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from app.db import init_db
from app.config import settings
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('db_schema_check.log')
    ]
)
logger = logging.getLogger(__name__)

# Log environment variables (without sensitive data)
logger.info(f"DATABASE_URL: {'set' if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL else 'not set'}")
logger.info(f"Environment: {os.environ.get('ENV', 'development')}")
logger.info(f"Working directory: {os.getcwd()}")

# Log the database URL (masking password)
if hasattr(settings, 'DATABASE_URL') and settings.DATABASE_URL:
    from urllib.parse import urlparse, urlunparse
    try:
        db_url = urlparse(settings.DATABASE_URL)
        if db_url.password:
            masked_url = db_url._replace(netloc=f"{db_url.username}:****@{db_url.hostname}" + 
                                       (f":{db_url.port}" if db_url.port else ""))
            logger.info(f"Database: {urlunparse(masked_url)}")
    except Exception as e:
        logger.warning(f"Could not parse DATABASE_URL: {e}")

async def check_database_schema():
    logger.info("=" * 50)
    logger.info("Starting database schema check...")
    logger.info("-" * 50)
    
    try:
        # Initialize the database (this will run our schema updates)
        await init_db()
        logger.info("✅ Database schema is up to date")
        
        # Verify the jobs table has the idempotency_key column
        from sqlalchemy import inspect, text
        from app.db import engine
        
        with engine.connect() as conn:
            # Check if jobs table exists
            inspector = inspect(engine)
            if not inspector.has_table("jobs"):
                logger.warning("❌ Jobs table does not exist")
                return False
                
            # Check for idempotency_key column
            columns = [col['name'] for col in inspector.get_columns('jobs')]
            if 'idempotency_key' not in columns:
                logger.error("❌ idempotency_key column is missing from jobs table")
                return False
                
            logger.info("✅ jobs table has idempotency_key column")
            
            # Check if the index exists (PostgreSQL specific)
            if engine.dialect.name == 'postgresql':
                result = conn.execute(text("""
                    SELECT 1 
                    FROM pg_indexes 
                    WHERE tablename = 'jobs' 
                    AND indexname = 'ix_jobs_idempotency_key'
                """))
                if not result.scalar():
                    logger.warning("⚠️  idempotency_key index not found. This is not critical but recommended for performance.")
                else:
                    logger.info("✅ idempotency_key index exists")
            
            logger.info("-" * 50)
            logger.info("✅ Database schema check completed successfully")
            logger.info("=" * 50)
            return True
            
    except Exception as e:
        logger.error("-" * 50)
        logger.error(f"❌ Error checking database schema: {e}", exc_info=True)
        logger.error("=" * 50)
        return False

if __name__ == "__main__":
    logger.info("Starting database schema check...")
    asyncio.run(check_database_schema())
