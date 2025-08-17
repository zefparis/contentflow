import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname='railway',
            user='postgres',
            password='GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            host='shortline.proxy.rlwy.net',
            port='24501',
            connect_timeout=5
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        return conn
    except Exception as e:
        print_error(f"Failed to connect to the database: {e}")
        return None

def check_table_exists(conn, table_name):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        return cur.fetchone()[0]

def setup_database():
    print("Setting up database...")
    
    # Connect to the database
    conn = get_connection()
    if not conn:
        print_error("Could not connect to the database. Please check your connection parameters.")
        return False
    
    try:
        with conn.cursor() as cur:
            # Check if jobs table exists
            if not check_table_exists(conn, 'jobs'):
                print("Creating 'jobs' table...")
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
                """)
                print_success("'jobs' table created successfully")
            else:
                print_success("'jobs' table already exists")
                
                # Check if idempotency_key column exists
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='jobs' AND column_name='idempotency_key';
                """)
                
                if not cur.fetchone():
                    print("Adding 'idempotency_key' column to 'jobs' table...")
                    cur.execute("""
                        ALTER TABLE public.jobs 
                        ADD COLUMN idempotency_key VARCHAR(32) UNIQUE;
                    """)
                    print_success("'idempotency_key' column added successfully")
                else:
                    print_success("'idempotency_key' column already exists")
            
            # Check if index on idempotency_key exists
            cur.execute("""
                SELECT indexname 
                FROM pg_indexes 
                WHERE tablename = 'jobs' 
                AND indexdef LIKE '%idempotency_key%';
            """)
            
            if not cur.fetchone():
                print("Creating index on 'idempotency_key'...")
                cur.execute("""
                    CREATE INDEX idx_jobs_idempotency_key 
                    ON public.jobs (idempotency_key);
                """)
                print_success("Index on 'idempotency_key' created successfully")
            else:
                print_success("Index on 'idempotency_key' already exists")
            
            return True
            
    except Exception as e:
        print_error(f"Error setting up database: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    if setup_database():
        print("\n✅ Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed. Please check the error messages above.")
