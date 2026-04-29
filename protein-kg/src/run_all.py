"""
一键运行：清洗 → 索引 → 压测 → API
"""
import sys, time, pickle
sys.path.insert(0, 'src')

print("=" * 50)
print("蛋白质平台 - 完整流程")
print("=" * 50)

from local_loader import LocalProteinLoader
from data_cleaner import ProteinDataCleaner
from embedding_service import ProteinEmbeddingService
from protein_recommender import ProteinRecommender
from multi_recall import ProteinMultiRecall
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# 1. 加载 + 清洗
cache = "../data/cleaned_cache.pkl"
if __import__('os').path.exists(cache):
    print("[1/4] 加载缓存...")
    with open(cache, 'rb') as f:
        cleaned = pickle.load(f)
else:
    print("[1/4] 加载并清洗...")
    loader = LocalProteinLoader("data/human_proteome_uncompressed.fasta")
    raw = loader.parse_fasta()
    cleaner = ProteinDataCleaner()
    cleaned = cleaner.clean_batch(raw, "UniProt")
    with open(cache, 'wb') as f:
        pickle.dump(cleaned, f)

print(f"   蛋白质: {len(cleaned)} 条")

# 2. 构建索引
print("[2/4] 构建索引...")
service = ProteinEmbeddingService()
t0 = time.time()
service.build_index(cleaned)
print(f"   耗时: {time.time()-t0:.1f}s")

# 3. 推荐引擎
print("[3/4] 初始化推荐引擎...")
rec = ProteinRecommender()
rec.build_from_proteins(cleaned, service)
multi = ProteinMultiRecall(rec)

# 4. 压测
print("[4/4] 压测...")
query = cleaned[0]["sequence"]

# 串行
t0 = time.time()
for _ in range(200):
    multi.recall(query, topk=200)
elapsed = time.time() - t0
print(f"   串行200次: {elapsed:.2f}s, QPS: {200/elapsed:.0f}")

# 并发
for w in [4, 8, 16]:
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=w) as ex:
        list(ex.map(lambda _: multi.recall(query, topk=200), range(500)))
    elapsed = time.time() - t0
    print(f"   并发{w} 500次: {elapsed:.2f}s, QPS: {500/elapsed:.0f}")

print("\n✅ 完成! 启动API: python api_server.py")