import subprocess
import sys

def run_psql_command(command):
    try:
        # Build the psql command
        psql_cmd = [
            'psql',
            '--host=shortline.proxy.rlwy.net',
            '--port=24501',
            '--username=postgres',
            '--dbname=railway',
            '--command=' + command
        ]
        
        # Set the PGPASSWORD environment variable
        env = {'PGPASSWORD': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy'}
        
        # Run the command
        result = subprocess.run(
            psql_cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        print(f"STDERR: {e.stderr}")
        return None

def main():
    print("Testing PostgreSQL connection...")
    
    # Test connection with a simple query
    output = run_psql_command("SELECT version();")
    
    if output:
        print("✅ Successfully connected to PostgreSQL!")
        print("\nPostgreSQL Version:")
        print(output)
        
        # Check if jobs table exists
        print("\nChecking if 'jobs' table exists...")
        output = run_psql_command("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'jobs'
            );
        """)
        
        if output and 't' in output.lower():
            print("✅ 'jobs' table exists")
            
            # Check if idempotency_key column exists
            print("\nChecking if 'idempotency_key' column exists...")
            output = run_psql_command("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='idempotency_key';
            """)
            
            if output and 'idempotency_key' in output:
                print("✅ 'idempotency_key' column exists")
                
                # Check for index on idempotency_key
                print("\nChecking for index on 'idempotency_key'...")
                output = run_psql_command("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'jobs' 
                    AND indexdef LIKE '%idempotency_key%';
                """)
                
                if output and output.strip():
                    print("✅ Index on 'idempotency_key' exists")
                    print(f"\nIndex details:\n{output}")
                else:
                    print("⚠️  No index found on 'idempotency_key'")
                    
                    # Create the index
                    print("\nCreating index on 'idempotency_key'...")
                    output = run_psql_command("""
                        CREATE INDEX IF NOT EXISTS idx_jobs_idempotency_key 
                        ON public.jobs (idempotency_key);
                    """)
                    
                    if output:
                        print("✅ Index created successfully")
                    else:
                        print("❌ Failed to create index")
            else:
                print("❌ 'idempotency_key' column is missing")
        else:
            print("❌ 'jobs' table does not exist")
    else:
        print("❌ Failed to connect to PostgreSQL")
        print("\nTroubleshooting steps:")
        print("1. Make sure psql is installed and in your PATH")
        print("2. Verify the database credentials are correct")
        print("3. Check if the database server is running and accessible")
        print("4. Check your network connection and firewall settings")

if __name__ == "__main__":
    main()
