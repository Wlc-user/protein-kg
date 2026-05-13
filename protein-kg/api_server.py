"""
蛋白质检索 API 服务 - 离线索引版 (性能定位 + 极速搜索版)
启动时从磁盘加载预构建的 Faiss 索引，无需重复编码
集成 DSSM 语义功能搜索，输出详细耗时分解，并提供极速相似蛋白搜索
"""
import sys, time, pickle
sys.path.insert(0, 'src')
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fast_embed import FastEmbeddingService

# ========== DSSM 相关导入 ==========
import os
import numpy as np
import faiss
import torch
from dssm.model import DualEncoder
from dssm.config import QUERY_ENCODER_PATH, DOC_ENCODER_PATH, FAISS_INDEX_PATH, ID_MAP_PATH

app = FastAPI(title="蛋白质智能检索API", version="2.0")

rec = None
multi_recall = None
dssm_model = None
dssm_index = None
dssm_id_map = None
service_global = None          # 全局的 FastEmbeddingService 实例

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
    global rec, multi_recall, dssm_model, dssm_index, dssm_id_map, service_global
    from local_loader import LocalProteinLoader
    from data_cleaner import ProteinDataCleaner
    from protein_recommender import ProteinRecommender
    from multi_recall import ProteinMultiRecall
    import faiss

    print("加载蛋白质数据...")
    loader = LocalProteinLoader("data/human_proteome_uncompressed.fasta")
    raw = loader.parse_fasta()
    cleaner = ProteinDataCleaner()
    cleaned = cleaner.clean_batch(raw, "UniProt")

    print("从磁盘加载预构建索引 (秒开)...")
    service = FastEmbeddingService(concurrency=200)

    index_path = "data/index/fast_embed.faiss"
    ids_path = "data/index/fast_embed_ids.pkl"

    service.index = faiss.read_index(index_path)
    with open(ids_path, 'rb') as f:
        service.protein_ids = pickle.load(f)

    # 保存为全局变量，供极速搜索使用
    service_global = service

    print(f"索引加载完成: {len(service.protein_ids)} 个向量")

    rec = ProteinRecommender()
    rec.build_from_proteins(cleaned, service)
    multi_recall = ProteinMultiRecall(rec)

    print(f"服务就绪: {len(cleaned)} 个蛋白质")

    # ========== 加载 DSSM 模型 ==========
    if os.path.exists(QUERY_ENCODER_PATH) and os.path.exists(DOC_ENCODER_PATH):
        dssm_model = DualEncoder(QUERY_ENCODER_PATH, DOC_ENCODER_PATH, projection_dim=256)
        print("✅ DSSM 模型加载完成")
    else:
        dssm_model = None
        print("⚠️ DSSM 模型文件缺失，/search/function 不可用")

    dssm_index = faiss.read_index(FAISS_INDEX_PATH)
    with open(ID_MAP_PATH, "rb") as f:
        dssm_id_map = pickle.load(f)
    print(f"✅ DSSM 功能搜索就绪，共 {dssm_index.ntotal} 条蛋白质")


@app.post("/search", response_model=List[SearchResult])
async def search(req: SearchRequest):
    t_start = time.time()

    # 1. 多路召回
    t_recall_start = time.time()
    results = multi_recall.recall(req.sequence, req.function_keyword, req.top_k * 3)
    t_recall = time.time() - t_recall_start

    # 2. 后处理
    t_post_start = time.time()
    items = []
    for pid, score in results[:req.top_k]:
        info = rec.protein_data.get(pid, {})
        items.append(SearchResult(
            protein_id=pid,
            name=info.get("name", "")[:80],
            similarity=round(float(score), 3),
            length=info.get("length", 0)
        ))
    t_post = time.time() - t_post_start

    t_total = time.time() - t_start
    print(f"⏱️  /search 耗时分解 | 召回:{t_recall*1000:.1f}ms | 后处理:{t_post*1000:.1f}ms | 总计:{t_total*1000:.1f}ms")
    return items


@app.get("/protein/{pid}")
async def get_protein(pid: str):
    info = rec.protein_data.get(pid, {})
    return {"protein_id": pid, "name": info.get("name",""), "length": info.get("length",0)}


@app.get("/search/function")
async def dssm_function_search(q: str, top_k: int = 10):
    """DSSM 语义搜索：输入功能关键词，返回相关蛋白质"""
    if dssm_model is None:
        return {"error": "DSSM 模型未加载"}

    t_start = time.time()

    # 1. 编码查询
    t_encode_start = time.time()
    with torch.no_grad():
        q_emb = dssm_model.encode_query([q])
    t_encode = time.time() - t_encode_start

    # 2. Faiss 搜索
    t_search_start = time.time()
    q_emb_np = q_emb.numpy().astype('float32')
    faiss.normalize_L2(q_emb_np)
    distances, indices = dssm_index.search(q_emb_np, top_k)
    t_search = time.time() - t_search_start

    # 3. 组装结果
    t_post_start = time.time()
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        protein_id = dssm_id_map[idx]
        info = rec.protein_data.get(protein_id, {})
        results.append({
            "protein_id": protein_id,
            "name": info.get("name", "")[:80],
            "similarity": round(float(dist), 4),
            "length": info.get("length", 0)
        })
    t_post = time.time() - t_post_start
    t_total = time.time() - t_start

    print(f"⏱️  /search/function 耗时分解 | 编码:{t_encode*1000:.1f}ms | Faiss搜索:{t_search*1000:.1f}ms | 组装:{t_post*1000:.1f}ms | 总计:{t_total*1000:.1f}ms")
    return {"query": q, "results": results}


@app.get("/search/fast")
async def search_fast(protein_id: str, top_k: int = 10):
    """
    极速相似蛋白搜索（基于预计算嵌入）
    输入蛋白质ID，返回最相似的蛋白质
    """
    if service_global is None:
        return {"error": "索引尚未加载"}

    if protein_id not in service_global.protein_ids:
        return {"error": f"蛋白质 {protein_id} 未在索引中"}

    # 获取该蛋白的向量
    idx_in_index = list(service_global.protein_ids).index(protein_id)
    vec = service_global.index.reconstruct(idx_in_index)
    vec = vec.reshape(1, -1).astype('float32')

    # 搜索（多取一个，为了过滤自身）
    t0 = time.time()
    distances, indices = service_global.index.search(vec, top_k + 1)
    t_search = time.time() - t0

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        pid = service_global.protein_ids[idx]
        if pid == protein_id:  # 跳过自身
            continue
        info = rec.protein_data.get(pid, {})
        results.append({
            "protein_id": pid,
            "name": info.get("name", "")[:80],
            "similarity": round(float(dist), 4),
            "length": info.get("length", 0)
        })
        if len(results) >= top_k:
            break

    total = time.time() - t0
    print(f"⏱️  /search/fast 耗时 | Faiss搜索:{t_search*1000:.1f}ms | 总计:{total*1000:.1f}ms")
    return {"query_id": protein_id, "results": results}


@app.get("/health")
async def health():
    return {"status": "ok", "total_proteins": len(rec.protein_ids)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)