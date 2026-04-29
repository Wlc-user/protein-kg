"""
蛋白质检索 API 服务
"""
import sys, time, pickle
sys.path.insert(0, 'src')
from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="蛋白质智能检索API", version="1.0")

rec = None
multi_recall = None

class SearchRequest(BaseModel):
    sequence: str = ""
    function_keyword: str = ""
    top_k: int = 10

class SearchResult(BaseModel):
    protein_id: str
    name: str
    similarity: float
    length: int

@app.on_event("startup")
async def startup():
    global rec, multi_recall
    from local_loader import LocalProteinLoader
    from data_cleaner import ProteinDataCleaner
    from embedding_service import ProteinEmbeddingService
    from protein_recommender import ProteinRecommender
    from multi_recall import ProteinMultiRecall
    
    print("加载蛋白质组...")
    loader = LocalProteinLoader("data/human_proteome_uncompressed.fasta")
    raw = loader.parse_fasta()
    cleaner = ProteinDataCleaner()
    cleaned = cleaner.clean_batch(raw, "UniProt")
    
    print("构建索引...")
    service = ProteinEmbeddingService()
    service.build_index(cleaned)
    rec = ProteinRecommender()
    rec.build_from_proteins(cleaned, service)
    multi_recall = ProteinMultiRecall(rec)
    
    print(f"✅ 服务就绪: {len(cleaned)} 个蛋白质")

@app.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    t0 = time.time()
    results = multi_recall.recall(req.sequence, req.function_keyword, req.top_k * 3)
    
    items = []
    for pid, score in results[:req.top_k]:
        info = rec.protein_data.get(pid, {})
        items.append(SearchResult(
            protein_id=pid,
            name=info.get("name", "")[:80],
            similarity=round(float(score), 3),
            length=info.get("length", 0)
        ))
    
    print(f"搜索耗时: {round((time.time()-t0)*1000, 1)}ms, 返回 {len(items)} 条")
    return items

@app.get("/protein/{pid}")
async def get_protein(pid: str):
    info = rec.protein_data.get(pid, {})
    return {"protein_id": pid, "name": info.get("name",""), "length": info.get("length",0)}

@app.get("/health")
async def health():
    return {"status": "ok", "total_proteins": len(rec.protein_ids)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)