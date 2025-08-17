import sys
import psycopg2
from psycopg2 import sql

def check_database():
    try:
        # Paramètres de connexion
        conn_params = {
            'host': 'shortline.proxy.rlwy.net',
            'port': 24501,
            'dbname': 'railway',
            'user': 'postgres',
            'password': 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy'
        }
        
        print("Connexion à la base de données...")
        conn = psycopg2.connect(**conn_params)
        print("✅ Connecté à la base de données avec succès!")
        
        # Vérifier les tables
        tables = ['jobs', 'runs']
        cursor = conn.cursor()
        
        for table in tables:
            # Vérifier si la table existe
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            
            exists = cursor.fetchone()[0]
            if exists:
                # Compter les lignes
                cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
                count = cursor.fetchone()[0]
                print(f"✅ Table '{table}' existe avec {count} lignes")
                
                # Afficher la structure
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """, (table,))
                
                print(f"   Structure de la table '{table}':")
                for col in cursor.fetchall():
                    print(f"   - {col[0]}: {col[1]} (Nullable: {col[2]})")
                
            else:
                print(f"❌ Table '{table}' n'existe pas")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Vérification de la base de données...")
    if check_database():
        print("\n✅ Vérification terminée avec succès!")
    else:
        print("\n❌ Des erreurs sont survenues lors de la vérification")
    
    input("\nAppuyez sur Entrée pour quitter...")
