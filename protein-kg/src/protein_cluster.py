# src/protein_cluster.py
import numpy as np
from sklearn.cluster import DBSCAN, HDBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from collections import defaultdict

class ProteinClusterer:
    """蛋白质序列聚类与功能分类"""
    
    def __init__(self, embeddings: np.ndarray, protein_ids: List[str]):
        self.embeddings = embeddings
        self.protein_ids = protein_ids
        self.labels = None
        self.clusters = defaultdict(list)
    
    def cluster_dbscan(self, eps=0.3, min_samples=3):
        """DBSCAN 聚类——自动发现离群点（噪声蛋白质）"""
        self.labels = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine').fit_predict(self.embeddings)
        self._build_clusters()
        return self._cluster_stats()
    
    def cluster_hdbscan(self, min_cluster_size=3):
        """HDBSCAN 聚类——不需要指定eps，自动适应密度"""
        self.labels = HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean').fit_predict(self.embeddings)
        self._build_clusters()
        return self._cluster_stats()
    
    def _build_clusters(self):
        """把聚类标签转成字典"""
        self.clusters = defaultdict(list)
        for i, label in enumerate(self.labels):
            self.clusters[int(label)].append({
                "protein_id": self.protein_ids[i],
                "embedding": self.embeddings[i]
            })
    
    def _cluster_stats(self):
        """聚类统计"""
        n_noise = len(self.clusters.get(-1, []))  # DBSCAN 用-1标记噪声
        n_clusters = len([k for k in self.clusters.keys() if k != -1])
        return {
            "total_clusters": n_clusters,
            "noise_points": n_noise,
            "cluster_sizes": {k: len(v) for k, v in self.clusters.items() if k != -1},
            "largest_cluster": max(len(v) for k, v in self.clusters.items() if k != -1) if n_clusters > 0 else 0
        }
    
    def find_similar(self, protein_id: str, top_k: int = 5):
        """找与某个蛋白质最相似的蛋白质"""
        if protein_id not in self.protein_ids:
            return []
        idx = self.protein_ids.index(protein_id)
        query_emb = self.embeddings[idx]
        
        # 余弦相似度
        sims = np.dot(self.embeddings, query_emb) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_emb) + 1e-8
        )
        top_idx = np.argsort(sims)[::-1][1:top_k+1]  # 跳过自己
        
        return [
            {"protein_id": self.protein_ids[i], "similarity": float(sims[i])}
            for i in top_idx
        ]
    
    def assign_function_by_majority(self, protein_functions: Dict[str, str]):
        """基于聚类结果做功能分类——同一个簇的蛋白质投票决定功能"""
        cluster_functions = {}
        for label, members in self.clusters.items():
            if label == -1:
                continue
            # 投票：簇内出现最多的功能
            funcs = [protein_functions.get(m["protein_id"], "unknown") for m in members]
            most_common = max(set(funcs), key=funcs.count)
            cluster_functions[label] = {
                "function": most_common,
                "members": len(members),
                "confidence": funcs.count(most_common) / len(funcs)
            }
        return cluster_functions
    
    def visualize_clusters(self, save_path="reports/protein_clusters.png"):
        """t-SNE 可视化聚类结果"""
        import matplotlib.pyplot as plt
        
        # 降维到2D
        tsne = TSNE(n_components=2, random_state=42)
        embeddings_2d = tsne.fit_transform(self.embeddings)
        
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(
            embeddings_2d[:, 0], embeddings_2d[:, 1],
            c=self.labels, cmap='tab20', alpha=0.7, s=50
        )
        plt.colorbar(scatter, label='Cluster')
        plt.title(f'蛋白质序列聚类 ({len(set(self.labels)) - (1 if -1 in self.labels else 0)} 个簇)')
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        return save_path