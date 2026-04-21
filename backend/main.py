from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.rag_engine import RAGEngine
#from backend.config import Settings
import uvicorn
from backend.ingestion import run_ingestion
from fastapi import BackgroundTasks

app = FastAPI(title="Ledical Literature Assistant API")
rag_engine = RAGEngine()

class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

'''
@app.post("/ingest")
async def ingest_data():
    try:
        run_ingestion("data")
        return {'message': "Ingestion completed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''


@app.post("/ingest")
async def ingest(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_ingestion, "data")
    return {"message": "Ingestion started"}


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    try:
        result = rag_engine.query(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)