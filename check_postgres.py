import os
import sys
import psycopg2
from psycopg2 import OperationalError

def check_postgres_connection():
    db_params = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
        'host': 'shortline.proxy.rlwy.net',
        'port': '24501'
    }
    
    print("Testing PostgreSQL connection...")
    print(f"Host: {db_params['host']}")
    print(f"Port: {db_params['port']}")
    print(f"Database: {db_params['dbname']}")
    
    try:
        # Try to connect to the database
        conn = psycopg2.connect(**db_params)
        print("✅ Successfully connected to PostgreSQL!")
        
        # Create a cursor
        cur = conn.cursor()
        
        # Check PostgreSQL version
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        
        # Check if jobs table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'jobs'
            );
        """)
        
        if cur.fetchone()[0]:
            print("✅ 'jobs' table exists")
            
            # Check if idempotency_key column exists
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='jobs' AND column_name='idempotency_key';
            """)
            
            if cur.fetchone():
                print("✅ 'idempotency_key' column exists in jobs table")
                
                # Check for index on idempotency_key
                cur.execute("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'jobs' 
                    AND indexdef LIKE '%idempotency_key%';
                """)
                
                if cur.fetchone():
                    print("✅ Index on 'idempotency_key' exists")
                else:
                    print("⚠️  No index found on 'idempotency_key' (recommended for performance)")
            else:
                print("❌ 'idempotency_key' column is missing from jobs table")
        else:
            print("❌ 'jobs' table does not exist")
        
        # Close the cursor and connection
        cur.close()
        conn.close()
        
    except OperationalError as e:
        print(f"❌ Could not connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify the database credentials are correct")
        print("2. Check if the database server is running and accessible")
        print("3. Verify the network connection to the database host")
        print("4. Check if the database 'railway' exists")
        print("5. Verify the user 'postgres' has necessary permissions")
        return False
    
    return True

if __name__ == "__main__":
    check_postgres_connection()
