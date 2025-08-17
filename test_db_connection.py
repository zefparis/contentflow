import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

def test_connection():
    # Get the database URL from environment variable or use the provided one
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy@shortline.proxy.rlwy.net:24501/railway")
    
    print(f"Testing connection to: {db_url.split('@')[-1]}")
    
    try:
        # Create engine with increased connection timeout
        engine = create_engine(
            db_url,
            connect_args={"connect_timeout": 10},
            pool_pre_ping=True
        )
        
        # Test connection
        with engine.connect() as conn:
            # Check PostgreSQL version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Successfully connected to PostgreSQL: {version}")
            
            # Check if jobs table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'jobs'
                );
            """))
            
            if result.scalar():
                print("✅ 'jobs' table exists")
                
                # Check if idempotency_key column exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='jobs' AND column_name='idempotency_key';
                """))
                
                if result.fetchone():
                    print("✅ 'idempotency_key' column exists in jobs table")
                    
                    # Check for index on idempotency_key
                    result = conn.execute(text("""
                        SELECT indexname 
                        FROM pg_indexes 
                        WHERE tablename = 'jobs' 
                        AND indexdef LIKE '%idempotency_key%';
                    """))
                    
                    if result.fetchone():
                        print("✅ Index on 'idempotency_key' exists")
                    else:
                        print("⚠️  No index found on 'idempotency_key' (recommended for performance)")
                else:
                    print("❌ 'idempotency_key' column is missing from jobs table")
            else:
                print("❌ 'jobs' table does not exist")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to the database: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
