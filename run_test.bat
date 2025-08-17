@echo off
echo Testing PostgreSQL connection...
python -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='railway',
        user='postgres',
        password='GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
        host='shortline.proxy.rlwy.net',
        port='24501',
        connect_timeout=5
    )
    print('✅ Successfully connected to PostgreSQL')
    
    cursor = conn.cursor()
    cursor.execute(\"SELECT version()\")
    print(f'PostgreSQL version: {cursor.fetchone()[0]}')
    
    cursor.execute(\"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'runs'
        )
    \""")
    
    if cursor.fetchone()[0]:
        print(\"✅ 'runs' table exists\")
        
        cursor.execute(\"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'runs'
            ORDER BY ordinal_position;
        \""")
        
        print(\"\\n'runs' table structure:\")
        for col in cursor.fetchall():
            print(f\"   - {col[0]}: {col[1]} (Nullable: {col[2]})\")
            
        cursor.execute(\"SELECT COUNT(*) FROM runs\")
        print(f\"\\n'runs' table has {cursor.fetchone()[0]} records\")
    else:
        print(\"❌ 'runs' table does not exist\")
        
except Exception as e:
    print(f'❌ Connection failed: {e}')
    
finally:
    if 'conn' in locals():
        conn.close()
"
pause
