import asyncio
import sys
from pathlib import Path
import os

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import inspect, text
from app.db import engine, init_db, Base
from app.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

async def initialize_database():
    print("=" * 80)
    print("DATABASE INITIALIZATION")
    print("=" * 80)
    
    try:
        # Initialize the database
        logger.info("Initializing database...")
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Verify the schema
        async with engine.connect() as conn:
            inspector = inspect(engine)
            
            # Check if jobs table exists
            if not inspector.has_table("jobs"):
                logger.error("❌ 'jobs' table was not created")
                return False
                
            # Check columns in jobs table
            columns = inspector.get_columns('jobs')
            column_names = [col['name'] for col in columns]
            
            print("\nJobs table columns:")
            print("-" * 40)
            for col in columns:
                print(f"- {col['name']}: {col['type']}")
            
            # Verify idempotency_key column
            if 'idempotency_key' not in column_names:
                logger.error("\n❌ 'idempotency_key' column is missing from jobs table")
                return False
                
            logger.info("\n✅ 'idempotency_key' column exists in jobs table")
            
            # Verify index on idempotency_key
            if engine.dialect.name == 'postgresql':
                result = await conn.execute(text("""
                    SELECT 1 
                    FROM pg_indexes 
                    WHERE tablename = 'jobs' 
                    AND indexname = 'ix_jobs_idempotency_key'
                
                """))
                if not result.scalar():
                    logger.warning("\n⚠️  Index 'ix_jobs_idempotency_key' is missing (recommended for performance)")
                else:
                    logger.info("\n✅ Index 'ix_jobs_idempotency_key' exists")
            
            return True
            
    except Exception as e:
        logger.error(f"\n❌ Error initializing database: {e}", exc_info=True)
        return False
    finally:
        await engine.dispose()
        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(initialize_database())
