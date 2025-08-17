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
            
            # Check and create runs table if it doesn't exist
            if not check_table_exists(conn, 'runs'):
                print("\nCreating 'runs' table...")
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
                
                # Check if we need to add any missing columns
                required_columns = {
                    'id', 'status', 'kind', 'details', 'started_at', 
                    'completed_at', 'error', 'created_at', 'updated_at'
                }
                existing_columns = {col[0] for col in columns}
                missing_columns = required_columns - existing_columns
                
                if missing_columns:
                    print(f"\nAdding missing columns to 'runs' table: {', '.join(missing_columns)}")
                    for column in missing_columns:
                        if column == 'id':
                            continue  # Skip primary key
                            
                        data_type = 'VARCHAR(50)'
                        if column in ('details', 'error'):
                            data_type = 'TEXT'
                        elif column in ('started_at', 'completed_at', 'created_at', 'updated_at'):
                            data_type = 'TIMESTAMP WITH TIME ZONE'
                        elif column == 'status':
                            data_type = 'VARCHAR(20)'
                        
                        try:
                            if column in ('created_at', 'updated_at'):
                                default = "DEFAULT NOW()"
                            elif column == 'status':
                                default = "DEFAULT 'pending'::character varying"
                            else:
                                default = ""
                                
                            cur.execute(f"""
                                ALTER TABLE public.runs 
                                ADD COLUMN {column} {data_type} {default};
                            """)
                            print_success(f"Added column '{column}' to 'runs' table")
                        except Exception as e:
                            print_error(f"Failed to add column '{column}': {e}")
                            conn.rollback()
            
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
