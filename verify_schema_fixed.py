import os
import sys
from pathlib import Path
import asyncio

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, inspect, text
from app.db import Base, init_db
from app.config import settings

async def verify_schema():
    print("=" * 50)
    print("VERIFYING DATABASE SCHEMA")
    print("=" * 50)
    
    # Use a test database
    test_db_path = "test_schema.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    settings.DATABASE_URL = f"sqlite:///{test_db_path}"
    
    try:
        # Initialize the database
        print("\nInitializing database...")
        await init_db()
        
        # Create engine and inspect
        engine = create_engine(settings.DATABASE_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\nCreated tables: {', '.join(tables)}")
        
        if 'jobs' not in tables:
            print("\n❌ ERROR: 'jobs' table was not created")
            return False
        
        # Check jobs table columns
        columns = inspector.get_columns('jobs')
        column_names = [col['name'] for col in columns]
        
        print("\nJobs table columns:")
        print("-" * 40)
        for col in columns:
            print(f"- {col['name']}: {col['type']}")
        
        # Verify idempotency_key column
        if 'idempotency_key' in column_names:
            print("\n✅ 'idempotency_key' column exists in jobs table")
            
            # Check for index
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='index' 
                    AND tbl_name='jobs'
                    AND sql LIKE '%idempotency_key%'
                
                """))
                index = result.scalar()
                
                if index:
                    print(f"✅ Found index on idempotency_key: {index}")
                else:
                    print("⚠️  No index found on idempotency_key (recommended for performance)")
            
            return True
        else:
            print("\n❌ 'idempotency_key' column is missing from jobs table")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    finally:
        print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(verify_schema())
