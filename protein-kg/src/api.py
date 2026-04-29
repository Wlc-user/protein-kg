from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import time

from data_loader import ProteinDataLoader
from graph_builder import ProteinGraphBuilder
from embedding_service import ProteinEmbeddingService

app = FastAPI(title="蛋白质知识图谱与检索API", version="1.0")

loader = ProteinDataLoader()
graph = ProteinGraphBuilder()
embedding_service = ProteinEmbeddingService()

class SearchRequest(BaseModel):
    sequence: str
    top_k: int = 5

class ProteinImportRequest(BaseModel):
    protein_ids: List[str]

@app.on_event("startup")
async def startup():
    """启动时预加载示例数据"""
    sample_ids = ["P04637", "P38398", "P00533"]
    proteins = loader.fetch_batch(sample_ids)
    
    if proteins:
        graph.import_batch(proteins)
        embedding_service.build_index(proteins)
        print(f"✅ 预加载 {len(proteins)} 个蛋白质")

@app.post("/import")
async def import_proteins(req: ProteinImportRequest):
    """导入蛋白质数据"""
    proteins = loader.fetch_batch(req.protein_ids)
    if not proteins:
        raise HTTPException(404, "未找到任何蛋白质数据")
    
    graph.import_batch(proteins)
    embedding_service.build_index(proteins)
    
    return {
        "imported": len(proteins),
        "protein_ids": [p["id"] for p in proteins]
    }

@app.post("/search/similar")
async def search_similar(req: SearchRequest):
    """搜索相似蛋白质序列"""
    t0 = time.time()
    results = embedding_service.search_similar(req.sequence, req.top_k)
    latency = (time.time() - t0) * 1000
    
    return {
        "query_length": len(req.sequence),
        "results": results,
        "latency_ms": round(latency, 2)
    }

@app.get("/protein/{protein_id}")
async def get_protein(protein_id: str):
    """查询蛋白质详情"""
    data = loader.fetch_protein(protein_id)
    if not data:
        raise HTTPException(404, f"蛋白质 {protein_id} 未找到")
    return data

@app.get("/graph/ppi/{protein_id}")
async def get_ppi(protein_id: str):
    """查询蛋白质相互作用网络"""
    network = graph.query_ppi_network(protein_id)
    return {
        "protein": protein_id,
        "interactions": len(network),
        "network": network
    }

@app.get("/graph/function/{keyword}")
async def search_function(keyword: str):
    """按功能搜索蛋白质"""
    results = graph.query_by_function(keyword)
    return {"keyword": keyword, "count": len(results), "proteins": results}

@app.get("/stats")
async def stats():
    """获取图谱统计"""
    return graph.get_statistics()

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)