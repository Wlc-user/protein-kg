"""
ETL 流水线：Extract(抽取) → Transform(清洗) → Load(加载) → Cluster(聚类)
"""
from data_loader import ProteinDataLoader
from local_loader import LocalProteinLoader
from data_cleaner import ProteinDataCleaner

class ProteinETLPipeline:
    
    def __init__(self):
        self.loader = ProteinDataLoader()
        self.cleaner = ProteinDataCleaner()
    
    def run_from_uniprot(self, protein_ids: list):
        print("=" * 60)
        print("🔬 ETL 流水线: UniProt → 清洗 → 聚类")
        print("=" * 60)
        
        print(f"\n📥 [Extract] 拉取 {len(protein_ids)} 个蛋白质...")
        raw_proteins = self.loader.fetch_batch(protein_ids)
        print(f"   成功: {len(raw_proteins)} 个")
        
        print(f"\n🧹 [Transform] 数据清洗...")
        cleaned = self.cleaner.clean_batch(raw_proteins, "UniProt")
        
        return cleaned
    
    def run_from_fasta(self, fasta_path: str):
        print("=" * 60)
        print("🔬 ETL 流水线: FASTA → 清洗 → 聚类")
        print("=" * 60)
        
        local_loader = LocalProteinLoader(fasta_path)
        raw_proteins = local_loader.parse_fasta()
        
        cleaned = self.cleaner.clean_batch(raw_proteins, "FASTA")
        return cleaned
    
    def run_clustering(self, proteins: list):
        """第三步：聚类分析"""
        print(f"\n🧬 [Cluster] 蛋白质序列聚类...")
        
        from embedding_service import ProteinEmbeddingService
        from chunk_processor import ProteinChunkProcessor
        from protein_cluster import ProteinClusterer
        
        # 分块
        chunker = ProteinChunkProcessor(chunk_size=50)
        chunks = chunker.chunk_by_length(proteins)
        print(f"   分块完成: {len(chunks)} 个桶")
        
        # 编码
        service = ProteinEmbeddingService()
        service.build_index(proteins)
        
        if len(proteins) < 3:
            print("   ⚠️ 蛋白质数量不足，跳过聚类")
            return proteins
        
        # 聚类
        clusterer = ProteinClusterer(
            service.embeddings if hasattr(service, 'embeddings') else None,
            service.protein_ids
        )
        stats = clusterer.cluster_hdbscan(min_cluster_size=2)
        
        print(f"   聚类结果: {stats['total_clusters']} 个簇, {stats['noise_points']} 个噪声点")
        for cid, size in stats['cluster_sizes'].items():
            print(f"   簇{cid}: {size} 个蛋白质")
        
        return proteins


if __name__ == "__main__":
    pipeline = ProteinETLPipeline()
    
    # 搜索癌症相关蛋白质（人工审核过的）
    print("搜索癌症相关蛋白质...")
    keywords = ['tumor', 'kinase', 'oncogene', 'apoptosis', 'DNA repair']
    all_ids = set()
    
    for kw in keywords:
        proteins = pipeline.loader.fetch_reviewed(kw, limit=10)
        for p in proteins:
            all_ids.add(p['id'])
    
    print(f"\n✅ 搜索完成: {len(all_ids)} 个不重复的高质量蛋白质")
    
    # ETL + 聚类
    cleaned = pipeline.run_from_uniprot(list(all_ids)[:20])  # 取前20个跑流程
    pipeline.run_clustering(cleaned)
    
    print(f"\n✅ 完成!")