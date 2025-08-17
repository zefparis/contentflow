@echo off
echo Testing PostgreSQL connection...
echo.
echo Attempting to connect to PostgreSQL server...

set PGPASSWORD=GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy
psql -h shortline.proxy.rlwy.net -p 5432 -U postgres -d railway -c "SELECT version();"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Successfully connected to PostgreSQL!
    echo.
    echo Running additional checks...
    echo.
    
    echo Checking if 'jobs' table exists...
    psql -h shortline.proxy.rlwy.net -p 5432 -U postgres -d railway -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'jobs');"
    
    echo.
    echo Checking if 'idempotency_key' column exists in 'jobs' table...
    psql -h shortline.proxy.rlwy.net -p 5432 -U postgres -d railway -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'jobs' AND column_name = 'idempotency_key';"
    
    echo.
    echo Checking for index on 'idempotency_key'...
    psql -h shortline.proxy.rlwy.net -p 5432 -U postgres -d railway -c "SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'jobs' AND indexdef LIKE '%idempotency_key%';"
) else (
    echo.
    echo ❌ Failed to connect to PostgreSQL.
    echo.
    echo Troubleshooting steps:
    echo 1. Make sure psql is installed and in your PATH
    echo 2. Verify the database credentials are correct
    echo 3. Check if the database server is running and accessible
    echo 4. Check your network connection and firewall settings
)

echo.
pause
