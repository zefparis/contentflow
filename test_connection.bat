@echo off
echo Testing database connection...

python -c "
import psycopg2
import sys

try:
    print('Connecting to database...')
    conn = psycopg2.connect(
        dbname='railway',
        user='postgres',
        password='GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
        host='shortline.proxy.rlwy.net',
        port='24501',
        connect_timeout=5
    )
    print('✅ Successfully connected to PostgreSQL!')
    
    with conn.cursor() as cur:
        # Get PostgreSQL version
        cur.execute('SELECT version()')
        print('\nPostgreSQL version:', cur.fetchone()[0])
        
        # Check if runs table exists
        cur.execute('''
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'runs'
            )
        ''')
        
        if cur.fetchone()[0]:
            print('\n✅ The "runs" table exists')
            
            # Get table structure
            cur.execute('''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'runs'
                ORDER BY ordinal_position;
            ''')
            
            print('\nTable structure:')
            for col in cur.fetchall():
                print(f'   - {col[0]}: {col[1]} (Nullable: {col[2]})')
            
            # Get record count
            cur.execute('SELECT COUNT(*) FROM runs')
            count = cur.fetchone()[0]
            print(f'\nThe "runs" table has {count} records')
        else:
            print('\n❌ The "runs" table does not exist')
    
    conn.close()
    
except Exception as e:
    print(f'\n❌ Error: {e}')
    print('\nTroubleshooting steps:')
    print('1. Verify the database server is running and accessible')
    print('2. Check the connection parameters (host, port, credentials)')
    print('3. Ensure your network connection is stable')
    print('4. Verify the database exists and the user has access')
    print('5. Check if a firewall is blocking the connection')
    
    # Print the full error details for debugging
    import traceback
    print('\nFull error details:')
    traceback.print_exc()
"

pause
