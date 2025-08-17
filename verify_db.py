import sys
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
        # Connection parameters
        conn_params = {
            'dbname': 'railway',
            'user': 'postgres',
            'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            'host': 'shortline.proxy.rlwy.net',
            'port': '24501',
            'connect_timeout': 5
        }
        
        print("Attempting to connect to PostgreSQL...")
        print(f"Host: {conn_params['host']}")
        print(f"Port: {conn_params['port']}")
        print(f"Database: {conn_params['dbname']}")
        
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print_success("Successfully connected to PostgreSQL!")
        return conn
        
    except Exception as e:
        print_error(f"Failed to connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify the database server is running and accessible")
        print("2. Check the connection parameters (host, port, credentials)")
        print("3. Ensure your network connection is stable")
        print("4. Verify the database 'railway' exists and the user has access")
        print("5. Check if a firewall is blocking the connection")
        return None

def check_table_exists(conn, table_name):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            return cur.fetchone()[0]
    except Exception as e:
        print_error(f"Error checking if table '{table_name}' exists: {e}")
        return False

def setup_database():
    print("\nSetting up database...")
    
    # Connect to the database
    conn = get_connection()
    if not conn:
        return False
    
    try:
        # Check if jobs table exists
        if not check_table_exists(conn, 'jobs'):
            print("Creating 'jobs' table...")
            with conn.cursor() as cur:
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
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'jobs' 
                AND column_name = 'idempotency_key';
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
        with conn.cursor() as cur:
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
        
        # Check if runs table exists
        if not check_table_exists(conn, 'runs'):
            print("\nCreating 'runs' table...")
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE public.runs (
                        id SERIAL PRIMARY KEY,
                        status VARCHAR(20) DEFAULT 'pending',
                        kind VARCHAR(50),
                        details TEXT,
                        started_at TIMESTAMP WITH TIME ZONE,
                        completed_at TIMESTAMP WITH TIME ZONE,
                        error TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                    
                    CREATE INDEX idx_runs_status ON public.runs (status);
                    CREATE INDEX idx_runs_kind ON public.runs (kind);
                    CREATE INDEX idx_runs_created_at ON public.runs (created_at);
                    
                    COMMENT ON TABLE public.runs IS 'Tracks execution runs of various jobs';
                    COMMENT ON COLUMN public.runs.status IS 'pending, running, completed, failed';
                    COMMENT ON COLUMN public.runs.kind IS 'Type of run (import, export, publish, etc.)';
                    COMMENT ON COLUMN public.runs.details IS 'JSON details about the run';
                """)
                print_success("'runs' table created successfully with indexes")
        else:
            print_success("'runs' table already exists")
            
            # Verify runs table structure
            with conn.cursor() as cur:
                print("\nChecking 'runs' table structure...")
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'runs'
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                print("\n'runs' table structure:")
                for col in columns:
                    print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
                
                # Check record count
                cur.execute("SELECT COUNT(*) FROM runs")
                count = cur.fetchone()[0]
                print(f"\n'runs' table has {count} records")
        
        return True
        
    except Exception as e:
        print_error(f"Error setting up database: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("PostgreSQL Database Setup and Verification")
    print("=" * 60)
    
    if setup_database():
        print("\n✅ Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed. Please check the error messages above.")
    
    input("\nPress Enter to exit...")
