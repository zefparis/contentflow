import psycopg2

try:
    # Connexion à la base de données
    conn = psycopg2.connect(
        host='shortline.proxy.rlwy.net',
        port=24501,
        dbname='railway',
        user='postgres',
        password='GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy'
    )
    
    print("✅ Connecté à la base de données avec succès!")
    
    # Créer un curseur
    cur = conn.cursor()
    
    # Vérifier les tables
    tables = ['jobs', 'runs']
    
    for table in tables:
        # Vérifier si la table existe
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table,))
        
        exists = cur.fetchone()[0]
        if exists:
            # Compter les lignes
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"✅ Table '{table}' existe avec {count} lignes")
            
            # Afficher les colonnes
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s
                ORDER BY ordinal_position;
            """, (table,))
            
            print(f"   Colonnes de la table '{table}':")
            for col in cur.fetchall():
                print(f"   - {col[0]} ({col[1]})")
        else:
            print(f"❌ Table '{table}' n'existe pas")
    
    # Fermer la connexion
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur: {e}")

input("\nAppuyez sur Entrée pour quitter...")
