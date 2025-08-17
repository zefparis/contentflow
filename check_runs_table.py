import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

def check_runs_table():
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Check if runs table exists
        with engine.connect() as conn:
            # For PostgreSQL
            result = conn.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'runs'
                );
                """)
            )
            table_exists = result.scalar()
            
            if table_exists:
                print("✅ The 'runs' table exists in the database.")
                # Get count of records in runs table
                count_result = conn.execute(text("SELECT COUNT(*) FROM runs"))
                count = count_result.scalar()
                print(f"   - Number of records: {count}")
                
                # Get table structure
                print("\nTable structure:")
                columns_result = conn.execute(
                    text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'runs'
                    ORDER BY ordinal_position;
                    """)
                )
                for col in columns_result:
                    print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
            else:
                print("❌ The 'runs' table does NOT exist in the database.")
                
    except Exception as e:
        print(f"❌ Error checking runs table: {e}")

if __name__ == "__main__":
    check_runs_table()
