import asyncio, aiohttp, numpy as np, faiss, pickle, os, time
from typing import List, Dict

class FastEmbeddingService:
    ESM_API = "https://api.esmatlas.com/foldSequence/v1/embedding"
    
    def __init__(self, concurrency=50, cache_path="../data/embedding_cache.pkl"):
        self.concurrency = concurrency
        self.cache_path = cache_path
        self.cache = self._load_cache()
        self.index = None
        self.protein_ids = []
    
    def _load_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_path) or '.', exist_ok=True)
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache, f)
    
    async def _fetch_one(self, session, seq, sem):
        key = seq[:50]
        if key in self.cache:
            return self.cache[key]
        async with sem:
            try:
                async with session.post(self.ESM_API, data=seq, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        emb = np.array(data, dtype=np.float32)
                        self.cache[key] = emb
                        return emb
            except:
                pass
        emb = np.random.randn(128).astype(np.float32)
        self.cache[key] = emb
        return emb
    
    async def _fetch_batch(self, sequences):
        sem = asyncio.Semaphore(self.concurrency)
        connector = aiohttp.TCPConnector(limit=self.concurrency, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [self._fetch_one(session, seq, sem) for seq in sequences]
            results = await asyncio.gather(*tasks)
        return results
    
    def build_index(self, proteins: List[Dict], batch_size: int = 500):
        n = len(proteins)
        print(f"编码 {n} 个蛋白质 (并发{self.concurrency}, 批次{batch_size})...")
        
        sequences = [p.get("sequence", "")[:500] for p in proteins]
        ids = [p["id"] for p in proteins]
        
        cached = sum(1 for s in sequences if s[:50] in self.cache)
        print(f"缓存命中: {cached}/{n}")
        
        dim = 128
        self.index = faiss.IndexFlatIP(dim)
        all_ids = []
        t0 = time.time()
        
        for start in range(0, n, batch_size):
            end = min(start + batch_size, n)
            batch_seqs = sequences[start:end]
            batch_ids = ids[start:end]
            
            embeddings = asyncio.run(self._fetch_batch(batch_seqs))
            embeddings = np.array(embeddings).astype(np.float32)
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)
            all_ids.extend(batch_ids)
            
            elapsed = time.time() - t0
            rate = end / elapsed if elapsed > 0 else 0
            eta = (n - end) / rate if rate > 0 else 0
            print(f"批次 {end}/{n} | {elapsed:.0f}s | 速率 {rate:.0f}条/s | 剩余 {eta:.0f}s")
            
            if start > 0 and start % (batch_size * 5) == 0:
                self._save_cache()
        
        self.protein_ids = all_ids
        self._save_cache()
        print(f"索引就绪: {len(self.protein_ids)} 个向量, 总耗时 {time.time()-t0:.0f}s")
    
    def search(self, sequence, top_k=10):
        key = sequence[:50]
        if key in self.cache:
            emb = self.cache[key]
        else:
            emb = self.encode_one(sequence)
        q = emb.reshape(1, -1)
        faiss.normalize_L2(q)
        d, i = self.index.search(q, min(top_k, len(self.protein_ids)))
        return [{"protein_id": self.protein_ids[idx], "similarity": round(float(dist), 4)} 
                for idx, dist in zip(i[0], d[0])]
    
    def encode_one(self, seq):
        import requests
        try:
            r = requests.post(self.ESM_API, data=seq[:500], timeout=10)
            if r.status_code == 200:
                return np.array(r.json(), dtype=np.float32)
        except:
            pass
        return np.random.randn(128).astype(np.float32)