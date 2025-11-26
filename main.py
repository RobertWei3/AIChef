from fastapi import FastAPI, HTTPException
from app.models import IngestRequest, GenerateRequest, FusionRequest
from app.ingestion import ingest_recipes
from app.rag import RecipeRAG
import os

app = FastAPI(title="食谱 RAG 助手 (Recipe RAG Assistant)")
rag_engine = RecipeRAG()

@app.post("/ingest")
async def ingest_data(request: IngestRequest):
    """
    导入食谱 JSON 数据集。
    """
    try:
        result = ingest_recipes(request.path)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_recipe(request: GenerateRequest):
    """
    根据食材生成食谱。
    """
    try:
        result = rag_engine.generate_recipe(request.ingredients, request.preferences)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fusion")
async def fuse_recipes(request: FusionRequest):
    """
    融合多个食谱。
    """
    try:
        result = rag_engine.fuse_recipes(request.ingredients)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "欢迎使用食谱 RAG 助手。请访问 /docs 查看 API 文档。"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
