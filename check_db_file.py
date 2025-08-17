import os
import sys

def check_db_file():
    db_path = "local.db"
    abs_path = os.path.abspath(db_path)
    
    print(f"Checking database file at: {abs_path}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Check if file exists
    if not os.path.exists(db_path):
        print("❌ Database file does not exist")
        return False
    
    # Get file info
    try:
        file_size = os.path.getsize(db_path)
        print(f"✅ Database file exists. Size: {file_size} bytes")
        return True
    except Exception as e:
        print(f"❌ Error accessing file: {e}")
        return False

if __name__ == "__main__":
    check_db_file()
