from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from core.chess_engine import get_engine
from core.chess_engine.exceptions import EngineError
import json

app = FastAPI(title="CataChess API")

# Initialize engine client (single-spot or multi-spot based on config)
engine = get_engine()


class AnalyzeRequest(BaseModel):
    fen: str
    depth: int = 15
    multipv: int = 3


@app.get("/")
async def root():
    return {"message": "CataChess API", "status": "running"}


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Analyze a chess position using the engine (non-streaming)
    """
    try:
        result = engine.analyze(
            fen=request.fen,
            depth=request.depth,
            multipv=request.multipv
        )
        return result
    except EngineError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analyze/stream")
async def analyze_stream(fen: str, depth: int = 15, multipv: int = 3):
    """
    Analyze a chess position using the engine (streaming)
    """
    try:
        result = engine.analyze(
            fen=fen,
            depth=depth,
            multipv=multipv
        )
        # For now, return the final result as a stream
        # In a real implementation, this would stream intermediate results
        async def generate():
            yield json.dumps(result.model_dump()) + "\n"

        return StreamingResponse(generate(), media_type="application/x-ndjson")
    except EngineError as e:
        raise HTTPException(status_code=500, detail=str(e))
