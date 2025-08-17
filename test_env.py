import sys
import os

def test_environment():
    print("Python Environment Test")
    print("=" * 50)
    
    # Print Python version
    print(f"Python Version: {sys.version}")
    print(f"Executable: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    
    # Test basic imports
    print("\nTesting imports...")
    try:
        import psycopg2
        print(f"✅ psycopg2 version: {psycopg2.__version__}")
    except ImportError:
        print("❌ psycopg2 is not installed")
    
    try:
        import sqlalchemy
        print(f"✅ SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        print("❌ SQLAlchemy is not installed")
    
    # Test file system access
    print("\nTesting file system access...")
    try:
        with open("test_file.txt", "w") as f:
            f.write("Test file content")
        os.remove("test_file.txt")
        print("✅ Successfully created and deleted a test file")
    except Exception as e:
        print(f"❌ File system access error: {e}")
    
    # Test environment variables
    print("\nEnvironment Variables:")
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # Mask password in the URL for security
        if "@" in db_url:
            user_pass, rest = db_url.split("@", 1)
            if "//" in user_pass and ":" in user_pass:
                protocol, credentials = user_pass.split("//", 1)
                user, password = credentials.split(":", 1)
                masked_url = f"{protocol}//{user}:*****@{rest}"
            else:
                masked_url = db_url
        else:
            masked_url = db_url
        print(f"DATABASE_URL: {masked_url}")
    else:
        print("❌ DATABASE_URL environment variable is not set")
    
    # Test basic Python functionality
    print("\nTesting basic Python functionality...")
    try:
        result = 2 + 2
        print(f"✅ 2 + 2 = {result} (Basic math works)")
    except Exception as e:
        print(f"❌ Basic Python functionality failed: {e}")

if __name__ == "__main__":
    test_environment()
    input("\nPress Enter to exit...")
