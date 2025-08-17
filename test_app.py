import sys
import asyncio
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import uvicorn
import os

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
app = FastAPI()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:GYnzpWkQwOMxPyovCIqAksEHlAHcRUQy@shortline.proxy.rlwy.net:24501/railway")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Test database connection
@app.get("/test-db")
async def test_db(db: Session = Depends(get_db)):
    try:
        # Execute a simple query
        result = db.execute(text("SELECT version()"))
        version = result.scalar()
        return {"status": "success", "database": "connected", "version": version}
    except Exception as e:
        return {"status": "error", "database": "connection failed", "error": str(e)}

# Test route
@app.get("/test")
async def test():
    return {"status": "ok", "message": "FastAPI is working"}

if __name__ == "__main__":
    uvicorn.run("test_app:app", host="0.0.0.0", port=8000, reload=True)
