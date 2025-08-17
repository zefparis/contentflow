import psycopg2
from psycopg2 import OperationalError

def test_connection():
    try:
        # Updated connection parameters with correct port 5432
        conn_params = {
            'dbname': 'railway',
            'user': 'postgres',
            'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            'host': 'shortline.proxy.rlwy.net',
            'port': '5432',  # Changed from 24501 to 5432
            'connect_timeout': 5
        }
        
        print("Testing PostgreSQL connection...")
        print(f"Host: {conn_params['host']}")
        print(f"Port: {conn_params['port']}")
        print(f"Database: {conn_params['dbname']}")
        
        # Try to connect to the database
        conn = psycopg2.connect(**conn_params)
        
        # Create a cursor to execute queries
        cur = conn.cursor()
        
        # Execute a simple query to check the connection
        print("\n✅ Successfully connected to PostgreSQL!")
        
        # Get PostgreSQL version
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"\nPostgreSQL Version:\n{version}")
        
        # Close the cursor and connection
        cur.close()
        conn.close()
        
        return True
        
    except OperationalError as e:
        print(f"\n❌ Could not connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if the database server is running")
        print("2. Verify the connection parameters (host, port, credentials)")
        print("3. Check your network connection and firewall settings")
        print("4. Ensure the database 'railway' exists and the user has access")
        return False
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        return False

if __name__ == "__main__":
    test_connection()
    input("\nPress Enter to exit...")
