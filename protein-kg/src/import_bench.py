import sys, time, numpy as np
sys.path.insert(0, 'src')
from local_loader import LocalProteinLoader
from data_cleaner import ProteinDataCleaner
from embedding_service import ProteinEmbeddingService
from protein_recommender import ProteinRecommender
from concurrent.futures import ThreadPoolExecutor
import sqlite3, os

print("=" * 50)
print("蛋白质平台 - 批量导入 + 高并发压测")
print("=" * 50)

# 1. 批量导入
print("\n[1/4] 批量导入人类蛋白质组...")
loader = LocalProteinLoader("data/human_proteome.fasta")
raw = loader.parse_fasta()
print(f"导入: {len(raw)} 条序列")

# 2. 清洗
print("\n[2/4] 清洗...")
cleaner = ProteinDataCleaner()
t0 = time.time()
cleaned = cleaner.clean_batch(raw, "UniProt")
print(f"清洗耗时: {time.time()-t0:.2f}s, {len(cleaned)} 条通过")

# 3. Faiss 索引
print("\n[3/4] 构建 Faiss 索引...")
service = ProteinEmbeddingService()
t0 = time.time()
service.build_index(cleaned)
print(f"索引构建: {time.time()-t0:.1f}s, {len(service.protein_ids)} 个向量")

# 4. 高并发压测
print("\n[4/4] 高并发压测...")
rec = ProteinRecommender()
rec.build_from_proteins(cleaned, service)

query = cleaned[0]["sequence"]

# 串行
t0 = time.time()
for _ in range(100):
    rec.recommend_by_sequence(query, top_k=10)
elapsed = time.time() - t0
print(f"串行 100次: {elapsed:.2f}s, QPS: {100/elapsed:.0f}")

# 并发 4/8/16
for workers in [4, 8, 16]:
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda _: rec.recommend_by_sequence(query, top_k=10), range(500)))
    elapsed = time.time() - t0
    print(f"并发{workers} 500次: {elapsed:.2f}s, QPS: {500/elapsed:.0f}")

print("\n✅ 完成")