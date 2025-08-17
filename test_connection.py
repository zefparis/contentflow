import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy import create_engine, inspect
from app.config import settings

def test_connection():
    print("Testing database connection...")
    
    # Get database URL
    db_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./local.db')
    print(f"Using database URL: {db_url}")
    
    # Create engine
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print("✅ Successfully connected to the database")
            
            # Check if we can list tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"\nFound {len(tables)} tables:")
            for table in tables:
                print(f"- {table}")
                
            # If jobs table exists, show its columns
            if 'jobs' in tables:
                print("\nJobs table columns:")
                print("-" * 40)
                columns = inspector.get_columns('jobs')
                for col in columns:
                    print(f"- {col['name']}: {col['type']}")
                
                # Check for idempotency_key
                has_idempotency_key = any(col['name'] == 'idempotency_key' for col in columns)
                if has_idempotency_key:
                    print("\n✅ 'idempotency_key' column exists in jobs table")
                else:
                    print("\n❌ 'idempotency_key' column is missing from jobs table")
            
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()
