import uvicorn
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI()

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
    return {"message": "FastAPI Test Application"}

@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Test connection with a simple query
        result = db.execute(text("SELECT version()"))
        version = result.scalar()
        return {"status": "success", "database": "connected", "version": version}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

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
            return {"status": "error", "message": "'runs' table does not exist"}
        
        # Try to query the runs table
        runs = db.execute(text("SELECT * FROM runs LIMIT 5")).fetchall()
        
        # Convert rows to list of dicts
        runs_data = [dict(row._mapping) for row in runs]
        
        return {
            "status": "success",
            "table_exists": True,
            "runs_count": len(runs_data),
            "runs": runs_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": str(e)})

if __name__ == "__main__":
    print("Starting FastAPI test server...")
    print(f"Database URL: {DATABASE_URL.split('@')[-1]}")
    uvicorn.run("test_fastapi_db:app", host="0.0.0.0", port=8000, reload=True)
