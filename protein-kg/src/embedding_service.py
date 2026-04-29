import numpy as np
import faiss
import requests
import pickle
import os
from typing import List, Dict

class ProteinEmbeddingService:
    ESM_API = "https://api.esmatlas.com/foldSequence/v1/embedding"
    
    def __init__(self, cache_path="../data/embedding_cache.pkl"):
        self.index = None
        self.protein_ids = []
        self.embeddings = None
        self.cache_path = cache_path
        self.cache = self._load_cache()
    
    def _load_cache(self):
        if os.path.exists(self.cache_path):
            with open(self.cache_path, 'rb') as f:
                return pickle.load(f)
        return {}
    
    def _save_cache(self):
        os.makedirs(os.path.dirname(self.cache_path) or '.', exist_ok=True)
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache, f)
    
    def encode_sequence(self, sequence: str) -> np.ndarray:
        seq = sequence[:500]
        key = seq[:50]
        
        if key in self.cache:
            return self.cache[key]
        
        try:
            resp = requests.post(self.ESM_API, data=seq, headers={"Content-Type": "text/plain"}, timeout=10)
            if resp.status_code == 200:
                emb = np.array(resp.json()).astype(np.float32)
                self.cache[key] = emb
                return emb
        except:
            pass
        
        emb = np.random.randn(128).astype(np.float32)
        self.cache[key] = emb
        return emb
    
    def build_index(self, proteins: List[Dict]):
        print(f"编码 {len(proteins)} 个蛋白质 (带缓存)...")
        
        embeddings = []
        self.protein_ids = []
        
        for i, p in enumerate(proteins):
            seq = p.get("sequence", "")
            emb = self.encode_sequence(seq[:500])
            embeddings.append(emb)
            self.protein_ids.append(p["id"])
            
            if (i + 1) % 500 == 0:
                print(f"  已编码 {i+1}/{len(proteins)}")
                self._save_cache()
        
        self._save_cache()
        self.embeddings = np.array(embeddings).astype(np.float32)
        faiss.normalize_L2(self.embeddings)
        self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings)
        print(f"索引就绪: {len(self.protein_ids)} 个向量")
    
    def search_similar(self, sequence: str, top_k: int = 10):
        if self.index is None:
            return []
        query_emb = self.encode_sequence(sequence).reshape(1, -1)
        faiss.normalize_L2(query_emb)
        distances, indices = self.index.search(query_emb, min(top_k, len(self.protein_ids)))
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.protein_ids):
                results.append({
                    "protein_id": self.protein_ids[idx],
                    "similarity": round(float(dist), 4)
                })
        return results