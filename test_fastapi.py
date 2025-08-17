import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# Test endpoint
@app.get("/test")
async def test():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("test_fastapi:app", host="0.0.0.0", port=8000, reload=True)
