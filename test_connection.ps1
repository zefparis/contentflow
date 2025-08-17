# PowerShell script to test PostgreSQL connection
Write-Host "Testing PostgreSQL connection..."

# Load the Npgsql assembly
Add-Type -Path "Npgsql.dll" -ErrorAction SilentlyContinue

if (-not (Get-Module -Name Npgsql -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Npgsql module..."
    Install-Module -Name Npgsql -Force -Scope CurrentUser
    Import-Module Npgsql
}

try {
    # Connection string
    $connString = "Host=shortline.proxy.rlwy.net;Port=24501;Database=railway;Username=postgres;Password=GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy;Timeout=5;"
    
    Write-Host "Connecting to database..."
    $conn = New-Object Npgsql.NpgsqlConnection($connString)
    $conn.Open()
    
    Write-Host "✅ Successfully connected to PostgreSQL!" -ForegroundColor Green
    
    # Get PostgreSQL version
    $cmd = $conn.CreateCommand()
    $cmd.CommandText = "SELECT version();"
    $version = $cmd.ExecuteScalar()
    Write-Host "`nPostgreSQL version: $version"
    
    # Check if runs table exists
    $cmd.CommandText = @"
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'runs'
    )
"@
    
    $tableExists = $cmd.ExecuteScalar()
    
    if ($tableExists) {
        Write-Host "`n✅ The 'runs' table exists" -ForegroundColor Green
        
        # Get table structure
        $cmd.CommandText = @"
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'runs'
        ORDER BY ordinal_position;
"@
        
        $reader = $cmd.ExecuteReader()
        
        Write-Host "`nTable structure:"
        while ($reader.Read()) {
            $colName = $reader["column_name"]
            $dataType = $reader["data_type"]
            $isNullable = $reader["is_nullable"]
            Write-Host "   - $colName : $dataType (Nullable: $isNullable)"
        }
        $reader.Close()
        
        # Get record count
        $cmd.CommandText = "SELECT COUNT(*) FROM runs"
        $count = $cmd.ExecuteScalar()
        Write-Host "`n'runs' table has $count records"
        
        if ($count -gt 0) {
            # Get sample records
            $cmd.CommandText = "SELECT * FROM runs ORDER BY created_at DESC LIMIT 3"
            $reader = $cmd.ExecuteReader()
            
            Write-Host "`nSample records:"
            while ($reader.Read()) {
                Write-Host "`nRun ID: $($reader[0])"
                Write-Host "Status: $($reader[1])"
                Write-Host "Kind: $($reader[2])"
                Write-Host "Created: $($reader[7])"
                Write-Host "---"
            }
            $reader.Close()
        }
    } else {
        Write-Host "`n❌ The 'runs' table does not exist" -ForegroundColor Red
    }
    
    $conn.Close()
    
} catch {
    Write-Host "`n❌ Error: $_" -ForegroundColor Red
    Write-Host "`nTroubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Verify the database server is running and accessible"
    Write-Host "2. Check the connection parameters (host, port, credentials)"
    Write-Host "3. Ensure your network connection is stable"
    Write-Host "4. Verify the database exists and the user has access"
    Write-Host "5. Check if a firewall is blocking the connection"
    
    # Print the full error details
    Write-Host "`nFull error details:" -ForegroundColor Yellow
    Write-Host $_.Exception
}

Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
