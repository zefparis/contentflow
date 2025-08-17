import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def test_connection():
    try:
        # Connection parameters
        conn_params = {
            'dbname': 'railway',
            'user': 'postgres',
            'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            'host': 'shortline.proxy.rlwy.net',
            'port': '5432',
            'connect_timeout': 5
        }
        
        print("Testing PostgreSQL connection...")
        print(f"Host: {conn_params['host']}")
        print(f"Port: {conn_params['port']}")
        print(f"Database: {conn_params['dbname']}")
        
        # Try to connect to the database
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print_success("Successfully connected to PostgreSQL!")
        
        # Get PostgreSQL version
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"\nPostgreSQL Version:\n{version}")
            
            # Check if jobs table exists
            print("\nChecking if 'jobs' table exists...")
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'jobs'
                );
            """)
            
            if cur.fetchone()[0]:
                print_success("'jobs' table exists")
                
                # Get table structure
                print("\nTable structure:")
                print("-" * 80)
                print(f"{'Column':<25} {'Type':<20} {'Nullable':<10} {'Default'}")
                print("-" * 80)
                
                cur.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'jobs'
                    ORDER BY ordinal_position;
                """)
                
                for col in cur.fetchall():
                    print(f"{col[0]:<25} {col[1]:<20} {col[2]:<10} {col[3] or ''}")
                
                # Check if idempotency_key exists
                print("\nChecking if 'idempotency_key' column exists...")
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='jobs' AND column_name='idempotency_key';
                """)
                
                if cur.fetchone():
                    print_success("'idempotency_key' column exists")
                    
                    # Check for index on idempotency_key
                    print("\nChecking for index on 'idempotency_key'...")
                    cur.execute("""
                        SELECT indexname, indexdef
                        FROM pg_indexes 
                        WHERE tablename = 'jobs' 
                        AND indexdef LIKE '%idempotency_key%';
                    """)
                    
                    index = cur.fetchone()
                    if index:
                        print_success(f"Index found: {index[0]}")
                        print(f"   Definition: {index[1]}")
                    else:
                        print("⚠️  No index found on 'idempotency_key'")
                        
                        # Create the index if it doesn't exist
                        try:
                            print("\nCreating index on 'idempotency_key'...")
                            cur.execute("""
                                CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key 
                                ON public.jobs (idempotency_key);
                            """)
                            print_success("Index created successfully")
                        except Exception as e:
                            print_error(f"Failed to create index: {e}")
                else:
                    print("❌ 'idempotency_key' column is missing")
                    
                    # Add the column if it doesn't exist
                    try:
                        print("\nAdding 'idempotency_key' column...")
                        cur.execute("""
                            ALTER TABLE public.jobs 
                            ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(32);
                            
                            CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key 
                            ON public.jobs (idempotency_key);
                        """)
                        print_success("Column and index added successfully")
                    except Exception as e:
                        print_error(f"Failed to add column: {e}")
            else:
                print("❌ 'jobs' table does not exist")
                
                # Create the table if it doesn't exist
                try:
                    print("\nCreating 'jobs' table...")
                    cur.execute("""
                        CREATE TABLE public.jobs (
                            id SERIAL PRIMARY KEY,
                            idempotency_key VARCHAR(32) UNIQUE,
                            payload JSONB,
                            status VARCHAR(50) DEFAULT 'queued',
                            attempts INTEGER DEFAULT 0,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            started_at TIMESTAMP WITH TIME ZONE,
                            completed_at TIMESTAMP WITH TIME ZONE,
                            result TEXT,
                            error TEXT
                        );
                        
                        CREATE INDEX idx_jobs_idempotency_key ON public.jobs (idempotency_key);
                        CREATE INDEX idx_jobs_status ON public.jobs (status);
                        CREATE INDEX idx_jobs_created_at ON public.jobs (created_at);
                    """)
                    print_success("'jobs' table created successfully with required schema")
                except Exception as e:
                    print_error(f"Failed to create table: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"An error occurred: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify the database credentials are correct")
        print("2. Check if the database server is running and accessible")
        print("3. Verify the network connection to the database host")
        print("4. Check if the database 'railway' exists")
        print("5. Verify the user 'postgres' has necessary permissions")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    test_connection()
    input("\nPress Enter to exit...")
