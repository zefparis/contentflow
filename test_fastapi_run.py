import uvicorn
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(title="Test FastAPI Run")

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy@shortline.proxy.rlwy.net:24501/railway")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "FastAPI Test Application - Database Connection Test"}

@app.get("/test-db")
async def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Test connection with a simple query
        result = db.execute(text("SELECT version()"))
        version = result.scalar()
        return {
            "status": "success",
            "database": "connected",
            "version": version
        }
    except Exception as e:
        return {
            "status": "error",
            "database": "connection failed",
            "error": str(e)
        }

@app.get("/test-runs")
async def test_runs(db: Session = Depends(get_db)):
    try:
        # Check if runs table exists
        result = db.execute(text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'runs'
            );
            """
        )
        
        if not result.scalar():
            return {
                "status": "error",
                "message": "'runs' table does not exist"
            }
        
        # Get runs table structure
        columns = db.execute(text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'runs'
            ORDER BY ordinal_position;
            """
        )
        
        # Get record count
        count_result = db.execute(text("SELECT COUNT(*) FROM runs"))
        count = count_result.scalar()
        
        # Get sample records
        runs = db.execute(text("SELECT * FROM runs ORDER BY created_at DESC LIMIT 5")).fetchall()
        
        # Convert rows to list of dicts
        runs_data = [dict(row._mapping) for row in runs]
        
        # Get column info
        columns_info = [
            {"name": col[0], "type": col[1], "nullable": col[2]}
            for col in columns
        ]
        
        return {
            "status": "success",
            "table_exists": True,
            "columns": columns_info,
            "record_count": count,
            "recent_runs": runs_data
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    print("Starting FastAPI test server...")
    print(f"Database URL: {DATABASE_URL.split('@')[-1]}")
    print("\nAvailable endpoints:")
    print("  - GET /: Basic test endpoint")
    print("  - GET /test-db: Test database connection")
    print("  - GET /test-runs: Test 'runs' table access")
    print("\nStarting server on http://0.0.0.0:8000")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "test_fastapi_run:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )
