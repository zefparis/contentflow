import psycopg2

try:
    conn = psycopg2.connect(
        host='shortline.proxy.rlwy.net',
        port=24501,
        dbname='railway',
        user='postgres',
        password='GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy'
    )
    print("✅ Connexion réussie à la base de données!")
    
    # Vérifier si la table 'runs' existe
    with conn.cursor() as cur:
        cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'runs')")
        if cur.fetchone()[0]:
            print("✅ La table 'runs' existe")
        else:
            print("❌ La table 'runs' n'existe pas")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Erreur: {e}")

input("Appuyez sur Entrée pour quitter...")
