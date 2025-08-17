import os
import sys
from sqlalchemy import create_engine, text, inspect
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
                
            # Check if runs table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'runs'
                );
            """))
            
            if result.scalar():
                print("✅ 'runs' table exists")
                
                # Get runs table structure
                print("\n'runs' table structure:")
                columns = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'runs'
                    ORDER BY ordinal_position;
                """))
                columns = columns.fetchall()
                for col in columns:
                    print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
                
                # Get record count
                count = conn.execute(text("SELECT COUNT(*) FROM runs")).scalar()
                print(f"\n'runs' table has {count} records")
                
            else:
                print("❌ 'runs' table does not exist")
                
                # Check if we can create the table
                try:
                    print("\nAttempting to create 'runs' table...")
                    conn.execute(text("""
                        CREATE TABLE runs (
                            id SERIAL PRIMARY KEY,
                            status VARCHAR(20) DEFAULT 'pending',
                            kind VARCHAR(50),
                            details TEXT,
                            started_at TIMESTAMP,
                            completed_at TIMESTAMP,
                            error TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        
                        CREATE INDEX idx_runs_status ON runs(status);
                        CREATE INDEX idx_runs_kind ON runs(kind);
                        CREATE INDEX idx_runs_created_at ON runs(created_at);
                        
                        COMMENT ON TABLE runs IS 'Tracks execution runs of various jobs';
                        COMMENT ON COLUMN runs.status IS 'pending, running, completed, failed';
                        COMMENT ON COLUMN runs.kind IS 'Type of run (import, export, publish, etc.)';
                        COMMENT ON COLUMN runs.details IS 'JSON details about the run';
                    """))
                    print("✅ Successfully created 'runs' table with indexes")
                    
                    # Verify the table was created
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM runs;
                    """))
                    print(f"'runs' table now has {result.scalar()} records")
                    
                except Exception as e:
                    print(f"❌ Failed to create 'runs' table: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect to the database: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()
