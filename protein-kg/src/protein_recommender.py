import numpy as np
import faiss

class ProteinRecommender:
    def __init__(self):
        self.index = None
        self.protein_ids = []
        self.protein_data = {}
        self.embeddings = None
    
    def build_from_proteins(self, proteins, embedding_service):
        self.protein_ids = [p["id"] for p in proteins]
        self.protein_data = {p["id"]: p for p in proteins}
        
        embeddings = []
        for p in proteins:
            seq = p.get("sequence", "")
            if seq:
                emb = embedding_service.encode_sequence(seq[:500])
            else:
                emb = np.random.randn(128).astype(np.float32)
            embeddings.append(emb)
        
        self.embeddings = np.array(embeddings).astype(np.float32)
        faiss.normalize_L2(self.embeddings)
        self.index = faiss.IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings)
        print(f"推荐引擎就绪: {len(self.protein_ids)} 个蛋白质")
    
    def recommend_by_sequence(self, query_sequence, top_k=10):
        from embedding_service import ProteinEmbeddingService
        service = ProteinEmbeddingService()
        query_emb = service.encode_sequence(query_sequence[:500])
        query_emb = query_emb.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_emb)
        
        distances, indices = self.index.search(query_emb, min(top_k * 3, len(self.protein_ids)))
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < len(self.protein_ids):
                pid = self.protein_ids[idx]
                results.append({
                    "protein_id": pid,
                    "similarity": round(float(dist), 4),
                    "rank_source": "sequence_similarity"
                })
        return results[:top_k]