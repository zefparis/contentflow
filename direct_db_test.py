import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def test_connection():
    # Load environment variables
    load_dotenv()
    
    # Get database URL from environment or use default
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy@shortline.proxy.rlwy.net:24501/railway")
    
    print(f"Testing connection to: {db_url.split('@')[-1]}")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        print_success("Successfully connected to the database!")
        
        # Check PostgreSQL version
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        
        # Check if runs table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'runs'
            );
        """)
        
        if cursor.fetchone()[0]:
            print_success("'runs' table exists in the database.")
            
            # Get runs table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'runs'
                ORDER BY ordinal_position;
            """)
            
            print("\n'runs' table structure:")
            for col in cursor.fetchall():
                print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
            
            # Get record count
            cursor.execute("SELECT COUNT(*) FROM runs")
            count = cursor.fetchone()[0]
            print(f"\n'runs' table has {count} records")
        else:
            print_error("'runs' table does NOT exist in the database.")
            
            # Create the runs table if it doesn't exist
            try:
                print("\nAttempting to create 'runs' table...")
                cursor.execute("""
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
                """)
                conn.commit()
                print_success("Successfully created 'runs' table with indexes")
            except Exception as e:
                print_error(f"Failed to create 'runs' table: {e}")
                conn.rollback()
        
        # Close the connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print_error(f"Failed to connect to the database: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify the database server is running and accessible")
        print("2. Check the connection parameters (host, port, credentials)")
        print("3. Ensure your network connection is stable")
        print("4. Verify the database exists and the user has access")
        print("5. Check if a firewall is blocking the connection")

if __name__ == "__main__":
    print("=" * 60)
    print("PostgreSQL Database Connection Test")
    print("=" * 60)
    test_connection()
    input("\nPress Enter to exit...")
