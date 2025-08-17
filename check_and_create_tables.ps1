# Script PowerShell pour vérifier et créer les tables si nécessaire

# Fonction pour afficher les messages de succès
function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

# Fonction pour afficher les messages d'erreur
function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

try {
    # Paramètres de connexion
    $dbParams = @{
        Host = 'shortline.proxy.rlwy.net'
        Port = '24501'
        Database = 'railway'
        Username = 'postgres'
        Password = 'GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy'
    }

    Write-Host "Connexion à la base de données..."
    
    # Chaîne de connexion
    $connString = "Host=$($dbParams.Host);Port=$($dbParams.Port);Database=$($dbParams.Database);Username=$($dbParams.Username);Password=$($dbParams.Password)"
    
    # Essayer de se connecter à la base de données
    $conn = New-Object Npgsql.NpgsqlConnection($connString)
    $conn.Open()
    
    Write-Success "Connecté à la base de données avec succès!"
    
    # Fonction pour exécuter une requête SQL
    function Invoke-SqlQuery {
        param([string]$query)
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = $query
        $cmd.ExecuteNonQuery()
    }
    
    # Fonction pour vérifier si une table existe
    function Test-TableExists {
        param([string]$tableName)
        $cmd = $conn.CreateCommand()
        $cmd.CommandText = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '$tableName')"
        $result = $cmd.ExecuteScalar()
        return $result -eq $true
    }
    
    # Vérifier et créer la table 'jobs' si nécessaire
    if (-not (Test-TableExists -tableName 'jobs')) {
        Write-Host "Création de la table 'jobs'..."
        $createJobsTable = @"
        CREATE TABLE public.jobs (
            id SERIAL PRIMARY KEY,
            idempotency_key VARCHAR(32) UNIQUE,
            payload JSONB,
            status VARCHAR(50) DEFAULT 'queued',
            attempts INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            result TEXT,
            error TEXT
        )
"@
        Invoke-SqlQuery -query $createJobsTable
        Write-Success "Table 'jobs' créée avec succès"
    } else {
        Write-Success "La table 'jobs' existe déjà"
    }
    
    # Vérifier et créer la table 'runs' si nécessaire
    if (-not (Test-TableExists -tableName 'runs')) {
        Write-Host "Création de la table 'runs'..."
        $createRunsTable = @"
        CREATE TABLE public.runs (
            id SERIAL PRIMARY KEY,
            status VARCHAR(20) DEFAULT 'pending',
            kind VARCHAR(50),
            details TEXT,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            error TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
"@
        Invoke-SqlQuery -query $createRunsTable
        
        # Créer les index pour la table 'runs'
        Invoke-SqlQuery -query "CREATE INDEX idx_runs_status ON public.runs (status)"
        Invoke-SqlQuery -query "CREATE INDEX idx_runs_kind ON public.runs (kind)"
        Invoke-SqlQuery -query "CREATE INDEX idx_runs_created_at ON public.runs (created_at)"
        
        # Ajouter les commentaires
        Invoke-SqlQuery -query "COMMENT ON TABLE public.runs IS 'Tracks execution runs of various jobs'"
        Invoke-SqlQuery -query "COMMENT ON COLUMN public.runs.status IS 'pending, running, completed, failed'"
        Invoke-SqlQuery -query "COMMENT ON COLUMN public.runs.kind IS 'Type of run (import, export, publish, etc.)'"
        Invoke-SqlQuery -query "COMMENT ON COLUMN public.runs.details IS 'JSON details about the run'"
        
        Write-Success "Table 'runs' créée avec succès avec ses index et commentaires"
    } else {
        Write-Success "La table 'runs' existe déjà"
    }
    
    # Vérifier les tables existantes
    Write-Host "`nVérification des tables..."
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = @"
    SELECT table_name, 
           (SELECT COUNT(*) FROM information_schema.tables t2 WHERE t2.table_name = t1.table_name) as exists,
           (SELECT COUNT(*) FROM information_schema.tables t2 WHERE t2.table_name = t1.table_name) as row_count
    FROM (SELECT 'jobs' as table_name
          UNION SELECT 'runs') t1
"@
    
    $reader = $cmd.ExecuteReader()
    
    Write-Host "`nÉtat des tables :"
    Write-Host "-----------------"
    while ($reader.Read()) {
        $tableName = $reader[0]
        $exists = $reader[1] -eq 1 ? "OUI" : "NON"
        Write-Host "Table: $tableName | Existe: $exists"
    }
    $reader.Close()
    
} catch {
    Write-Error "Erreur : $_"
    Write-Host "`nDétails de l'erreur :"
    $_.Exception.Message
    $_.ScriptStackTrace
} finally {
    if ($conn -ne $null) {
        $conn.Close()
        Write-Host "`nConnexion à la base de données fermée."
    }
}

Write-Host "`nAppuyez sur une touche pour continuer..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
