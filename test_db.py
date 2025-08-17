import sys
import psycopg2
from psycopg2 import OperationalError

def test_connection():
    print("Testing PostgreSQL connection...")
    
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
        
        print(f"Connecting to {conn_params['host']}:{conn_params['port']}...")
        
        # Try to connect to the database
        conn = psycopg2.connect(**conn_params)
        
        # Create a cursor to execute queries
        cur = conn.cursor()
        
        # Execute a simple query to check the connection
        print("\n✅ Successfully connected to PostgreSQL!")
        
        # Get PostgreSQL version
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
            print("✅ 'jobs' table exists")
            
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
                print("✅ 'idempotency_key' column exists")
                
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
                    print(f"✅ Index found: {index[0]}")
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
                        conn.commit()
                        print("✅ Index created successfully")
                    except Exception as e:
                        print(f"❌ Failed to create index: {e}")
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
                    conn.commit()
                    print("✅ Column and index added successfully")
                except Exception as e:
                    print(f"❌ Failed to add column: {e}")
        else:
            print("❌ 'jobs' table does not exist")
            
            # Create the table if it doesn't exist
            try:
                print("\nCreating 'jobs' table...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS public.jobs (
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
                    
                    CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key 
                    ON public.jobs (idempotency_key);
                """)
                conn.commit()
                print("✅ 'jobs' table created successfully")
            except Exception as e:
                print(f"❌ Failed to create table: {e}")
        
        # Close the cursor and connection
        cur.close()
        conn.close()
        
        return True
        
    except OperationalError as e:
        print(f"❌ Could not connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if the database server is running")
        print("2. Verify the connection parameters (host, port, credentials)")
        print("3. Check your network connection and firewall settings")
        print("4. Ensure the database 'railway' exists and the user has access")
        return False
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return False

if __name__ == "__main__":
    test_connection()
