import asyncio
import sys
from pathlib import Path
import os

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import inspect, text
from app.db import engine
from app.config import settings

def print_columns(columns):
    print("\nTable columns:")
    print("-" * 80)
    print(f"{'Name':<20} | {'Type':<20} | {'Nullable':<10} | {'Default':<20}")
    print("-" * 80)
    for col in columns:
        default = str(col.get('default', ''))
        if 'nextval' in default:  # Skip sequence defaults
            default = 'auto-increment'
        print(f"{col['name']:<20} | {str(col['type']):<20} | {str(col['nullable']):<10} | {default:<20}")

async def check_database():
    print("=" * 80)
    print("DATABASE SCHEMA VERIFICATION")
    print("=" * 80)
    
    # Get database URL (masking password)
    db_url = getattr(settings, 'DATABASE_URL', 'not set')
    if db_url != 'not set':
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        if parsed.password:
            masked_url = db_url.replace(f":{parsed.password}@", ":****@")
            print(f"\nDatabase: {masked_url}")
    
    # Check connection
    try:
        async with engine.connect() as conn:
            print("\n✅ Successfully connected to the database")
            
            # Check if jobs table exists
            inspector = inspect(engine)
            if not inspector.has_table("jobs"):
                print("\n❌ ERROR: 'jobs' table does not exist in the database")
                return
                
            # Get columns from jobs table
            columns = inspector.get_columns('jobs')
            print_columns(columns)
            
            # Check for idempotency_key column
            has_idempotency_key = any(col['name'] == 'idempotency_key' for col in columns)
            if has_idempotency_key:
                print("\n✅ 'idempotency_key' column exists in the jobs table")
            else:
                print("\n❌ 'idempotency_key' column is MISSING from the jobs table")
            
            # Check for index on idempotency_key
            if engine.dialect.name == 'postgresql':
                result = await conn.execute(text("""
                    SELECT 1 
                    FROM pg_indexes 
                    WHERE tablename = 'jobs' 
                    AND indexname = 'ix_jobs_idempotency_key'
                
                """))
                if result.scalar():
                    print("✅ Index 'ix_jobs_idempotency_key' exists")
                else:
                    print("⚠️  Index 'ix_jobs_idempotency_key' is missing (recommended for performance)")
            
    except Exception as e:
        print(f"\n❌ ERROR connecting to database: {e}")
    finally:
        print("\n" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(check_database())
