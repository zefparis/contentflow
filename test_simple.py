print("Python test script is running!")
print("Testing database connection...")

try:
    # Try to import required modules
    import psycopg2
    from psycopg2 import sql
    import os
    
    print("✅ Required modules are installed")
    
    # Database connection parameters
    db_params = {
        'dbname': 'railway',
        'user': 'postgres',
        'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
        'host': 'shortline.proxy.rlwy.net',
        'port': '24501'
    }
    
    print("Attempting to connect to the database...")
    
    # Try to connect to the database
    conn = psycopg2.connect(**db_params)
    print("✅ Successfully connected to the database!")
    
    # Create a cursor
    cur = conn.cursor()
    
    # Get PostgreSQL version
    cur.execute("SELECT version();")
    version = cur.fetchone()[0]
    print(f"PostgreSQL version: {version}")
    
    # Check if runs table exists
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'runs'
        );
    """)
    
    if cur.fetchone()[0]:
        print("✅ 'runs' table exists")
        
        # Get table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'runs'
            ORDER BY ordinal_position;
        """)
        
        print("\n'runs' table structure:")
        for col in cur.fetchall():
            print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
        
        # Get record count
        cur.execute("SELECT COUNT(*) FROM runs")
        count = cur.fetchone()[0]
        print(f"\n'runs' table has {count} records")
    else:
        print("❌ 'runs' table does not exist")
    
    # Close the cursor and connection
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    
input("\nPress Enter to exit...")
