import psycopg2
import os
from dotenv import load_dotenv

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def execute_sql_file(conn, file_path):
    try:
        with open(file_path, 'r') as file:
            sql_script = file.read()
        
        with conn.cursor() as cursor:
            cursor.execute(sql_script)
            
            # Si la requête retourne des résultats (comme notre SELECT final)
            if cursor.description:
                results = cursor.fetchall()
                print("\nRésultats de la création des tables :")
                print("-" * 50)
                for row in results:
                    table_name, exists, row_count = row
                    status = "EXISTE" if exists == 1 else "N'EXISTE PAS"
                    print(f"Table: {table_name:<10} | Statut: {status:<10} | Lignes: {row_count}")
        
        conn.commit()
        return True
    except Exception as e:
        print_error(f"Erreur lors de l'exécution du script SQL: {e}")
        conn.rollback()
        return False

def main():
    # Charger les variables d'environnement
    load_dotenv()
    
    # Paramètres de connexion
    db_params = {
        'dbname': os.getenv('DB_NAME', 'railway'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy'),
        'host': os.getenv('DB_HOST', 'shortline.proxy.rlwy.net'),
        'port': os.getenv('DB_PORT', '24501')
    }
    
    print("Connexion à la base de données...")
    try:
        conn = psycopg2.connect(**db_params)
        print_success("Connecté à la base de données avec succès!")
        
        # Exécuter le script SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'create_tables.sql')
        if os.path.exists(sql_file):
            print(f"\nExécution du script SQL: {sql_file}")
            if execute_sql_file(conn, sql_file):
                print_success("\nLes tables ont été créées avec succès!")
            else:
                print_error("\nErreur lors de la création des tables.")
        else:
            print_error(f"Le fichier {sql_file} est introuvable.")
            
    except Exception as e:
        print_error(f"Erreur de connexion à la base de données: {e}")
        print("\nVérifiez les paramètres de connexion dans le fichier .env ou directement dans le script.")
    finally:
        if 'conn' in locals():
            conn.close()
            print("\nConnexion à la base de données fermée.")

if __name__ == "__main__":
    print("=" * 60)
    print("Configuration de la base de données ContentFlow")
    print("=" * 60)
    main()
    input("\nAppuyez sur Entrée pour quitter...")
