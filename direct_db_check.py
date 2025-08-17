import sqlite3
import os
from pathlib import Path

def check_sqlite_db():
    db_path = Path("local.db")
    print(f"Checking SQLite database at: {db_path.absolute()}")
    
    if not db_path.exists():
        print("❌ Database file does not exist")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if jobs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'")
        if not cursor.fetchone():
            print("❌ 'jobs' table does not exist")
            return False
        
        # Get table info
        cursor.execute("PRAGMA table_info(jobs)")
        columns = cursor.fetchall()
        
        print("\nJobs table columns:")
        print("-" * 40)
        for col in columns:
            print(f"- {col[1]}: {col[2]} {'(PRIMARY KEY)' if col[5] else ''}")
        
        # Check for idempotency_key
        has_idempotency_key = any(col[1] == 'idempotency_key' for col in columns)
        
        if has_idempotency_key:
            print("\n✅ 'idempotency_key' column exists in jobs table")
            
            # Check for index on idempotency_key
            cursor.execute("PRAGMA index_list('jobs')")
            indexes = cursor.fetchall()
            has_index = False
            
            for index in indexes:
                cursor.execute(f"PRAGMA index_info({index[1]})")
                idx_columns = cursor.fetchall()
                if any(col[2] == 'idempotency_key' for col in idx_columns):
                    has_index = True
                    print(f"✅ Found index on idempotency_key: {index[1]}")
                    break
            
            if not has_index:
                print("⚠️  No index found on idempotency_key (recommended for performance)")
            
            return True
        else:
            print("\n❌ 'idempotency_key' column is missing from jobs table")
            return False
            
    except Exception as e:
        print(f"\n❌ Error checking database: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_sqlite_db()
