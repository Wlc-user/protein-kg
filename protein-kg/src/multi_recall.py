"""
蛋白质多路召回：序列 + 功能 + 结构 三路召回
"""
import numpy as np
from collections import defaultdict

class ProteinMultiRecall:
    def __init__(self, recommender):
        self.rec = recommender
    
    def recall(self, query_seq: str, query_func: str = "", topk: int = 200) -> list:
        merged = defaultdict(float)
        
        # 路1：序列相似性（Faiss）
        seq_results = self.rec.recommend_by_sequence(query_seq, top_k=topk)
        for r in seq_results:
            merged[r["protein_id"]] += r.get("similarity", 0) * 0.5  # 权重 0.5
        
        # 路2：功能关键词匹配
        if query_func:
            func_results = self._recall_by_function(query_func, topk)
            for r in func_results:
                merged[r["protein_id"]] += r.get("score", 0) * 0.3  # 权重 0.3
        
        # 路3：热门蛋白质兜底
        hot_results = self._recall_hot(topk // 3)
        for pid in hot_results:
            merged[pid] += 0.1  # 权重 0.1
        
        ranked = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        return ranked[:topk]
    
    def _recall_by_function(self, query_func: str, topk: int) -> list:
        results = []
        for pid, info in self.rec.protein_data.items():
            name = info.get("name", "").lower()
            if query_func.lower() in name:
                results.append({"protein_id": pid, "score": 0.8})
        return results[:topk]
    
    def _recall_hot(self, topk: int) -> list:
        sorted_by_len = sorted(self.rec.protein_data.items(), 
                               key=lambda x: x[1].get("length", 0), reverse=True)
        return [pid for pid, _ in sorted_by_len[:topk]]