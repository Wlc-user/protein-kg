import sys, time, numpy as np
sys.path.insert(0, 'src')
from data_loader import ProteinDataLoader
from data_cleaner import ProteinDataCleaner
from postgres_store import PostgresProteinStore as ProteinStore
from embedding_service import ProteinEmbeddingService
import requests

print("=" * 50)
print("蛋白质平台 - 全链路压测")
print("=" * 50)

# 1. 拉取数据
print("\n[1/4] 拉取数据...")
loader = ProteinDataLoader()
keywords = ['tumor', 'kinase', 'oncogene', 'apoptosis', 'DNA repair']
all_ids = set()

for kw in keywords:
    url = loader.BASE_URL + '/search?query=(' + kw + ')+AND+(reviewed:true)&size=10'
    r = requests.get(url, headers={'Accept': 'application/json'})
    if r.status_code == 200:
        for p in r.json().get('results', []):
            all_ids.add(p['primaryAccession'])

raw = loader.fetch_batch(list(all_ids))
print("拉取: " + str(len(raw)) + " 条")

# 2. 清洗
print("\n[2/4] 清洗...")
cleaner = ProteinDataCleaner()
t0 = time.time()
cleaned = cleaner.clean_batch(raw, "UniProt")
print("清洗耗时: " + str(round(time.time()-t0, 2)) + "s, " + str(len(cleaned)) + " 条通过")

# 3. 入库
print("\n[3/4] 入库(SQLite)...")
store = ProteinStore()
t0 = time.time()
store.insert_batch(cleaned)
print("写入耗时: " + str(round(time.time()-t0, 2)) + "s")

# 4. 向量检索压测
print("\n[4/4] Faiss检索压测...")
service = ProteinEmbeddingService()
service.build_index(cleaned)

query = cleaned[0]["sequence"]

# 串行
t0 = time.time()
for _ in range(1000):
    service.search_similar(query, top_k=10)
elapsed = time.time() - t0
print("串行1000次: " + str(round(elapsed, 2)) + "s, QPS: " + str(int(1000/elapsed)))

# 并发
from concurrent.futures import ThreadPoolExecutor
for workers in [4, 8, 16]:
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda _: service.search_similar(query, top_k=10), range(1000)))
    elapsed = time.time() - t0
    print("并发" + str(workers) + ": " + str(round(elapsed, 2)) + "s, QPS: " + str(int(1000/elapsed)))

store.close()
print("\n完成")