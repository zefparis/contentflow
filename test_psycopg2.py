import psycopg2
from psycopg2 import OperationalError

def test_connection():
    try:
        # Connection parameters
        conn_params = {
            'dbname': 'railway',
            'user': 'postgres',
            'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy',
            'host': 'shortline.proxy.rlwy.net',
            'port': '24501',
            'connect_timeout': 5
        }
        
        print("Attempting to connect to PostgreSQL...")
        connection = psycopg2.connect(**conn_params)
        
        print("✅ Successfully connected to PostgreSQL!")
        
        # Create a cursor to execute queries
        cursor = connection.cursor()
        
        # Execute a simple query to check the connection
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print(f"PostgreSQL version: {db_version[0]}")
        
        # Close the cursor and connection
        cursor.close()
        connection.close()
        
    except OperationalError as e:
        print(f"❌ Could not connect to PostgreSQL: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check if the database server is running and accessible")
        print("2. Verify the connection parameters (host, port, credentials)")
        print("3. Check your network connection and firewall settings")
        print("4. Ensure the database 'railway' exists and the user has access")
        return False
    
    return True

if __name__ == "__main__":
    test_connection()
