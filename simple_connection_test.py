import sys
import psycopg2
from psycopg2 import OperationalError

def test_connection():
    try:
        print("Attempting to connect to PostgreSQL database...")
        
        # Connection parameters
        conn_params = {
            'dbname': 'railway',
            'user': 'postgres',
            'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            'host': 'shortline.proxy.rlwy.net',
            'port': '5432',
            'connect_timeout': 10  # Increased timeout to 10 seconds
        }
        
        # Print connection details (without password)
        print(f"Host: {conn_params['host']}")
        print(f"Port: {conn_params['port']}")
        print(f"Database: {conn_params['dbname']}")
        print(f"User: {conn_params['user']}")
        
        # Try to connect to the database
        conn = psycopg2.connect(**conn_params)
        
        # If we get here, the connection was successful
        print("\n✅ Successfully connected to PostgreSQL!")
        
        # Get PostgreSQL version
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"\nPostgreSQL Version:\n{version}")
        
        return True
        
    except OperationalError as e:
        print(f"\n❌ Could not connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if the database server is running and accessible")
        print("2. Verify the connection parameters (host, port, credentials)")
        print("3. Check your network connection and firewall settings")
        print("4. Ensure the database 'railway' exists and the user has access")
        return False
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    
    test_connection()
    
    print("\n" + "=" * 60)
    input("Press Enter to exit...")
