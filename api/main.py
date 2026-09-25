from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from src.agent import TextToSQLAgent

app = FastAPI(title="Self-Correcting Text-to-SQL Engine")

class QueryRequest(BaseModel):
    question: str
    disable_semantics: Optional[bool] = False

class QueryResponse(BaseModel):
    status: str
    final_sql: Optional[str]
    results: Optional[List[Dict[str, Any]]]
    iterations: int
    repair_history: List[Dict[str, Any]]

@app.post("/api/query", response_model=QueryResponse)
def handle_query(request: QueryRequest):
    try:
        agent = TextToSQLAgent(max_attempts=3)
        result = agent.process_query(
            question=request.question, 
            disable_semantics=request.disable_semantics
        )
        return QueryResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
