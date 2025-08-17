import sys
import psycopg2

def main():
    print("Testing database connection...")
    
    try:
        # Connect to the database
        conn = psycopg2.connect(
            dbname='railway',
            user='postgres',
            password='GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            host='shortline.proxy.rlwy.net',
            port='24501',
            connect_timeout=5
        )
        
        print("✅ Successfully connected to PostgreSQL!")
        
        # Get PostgreSQL version
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"\nPostgreSQL version: {version}")
            
            # Check if runs table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'runs'
                );
            """)
            
            if cur.fetchone()[0]:
                print("\n✅ 'runs' table exists")
                
                # Get table structure
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'runs'
                    ORDER BY ordinal_position;
                """)
                
                print("\nTable structure:")
                for col in cur.fetchall():
                    print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
                
                # Get record count
                cur.execute("SELECT COUNT(*) FROM runs")
                count = cur.fetchone()[0]
                print(f"\n'runs' table has {count} records")
                
                if count > 0:
                    # Get sample records
                    cur.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT 3")
                    print("\nSample records:")
                    for row in cur.fetchall():
                        print(f"\nRun ID: {row[0]}")
                        print(f"Status: {row[1]}")
                        print(f"Kind: {row[2]}")
                        print(f"Created: {row[7]}")
            else:
                print("\n❌ 'runs' table does not exist")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify the database server is running and accessible")
        print("2. Check the connection parameters (host, port, credentials)")
        print("3. Ensure your network connection is stable")
        print("4. Verify the database exists and the user has access")
        print("5. Check if a firewall is blocking the connection")
        sys.exit(1)

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
