"""
STRING 数据库加载器：蛋白质相互作用网络
https://string-db.org/ - 最权威的蛋白质相互作用数据库
"""
import requests
import pandas as pd
from typing import List, Dict

class STRINGLoader:
    """从 STRING 数据库加载蛋白质相互作用数据"""
    
    BASE_URL = "https://string-db.org/api"
    
    def get_ppi_network(self, protein_ids: List[str], species: int = 9606) -> pd.DataFrame:
        """
        获取蛋白质相互作用网络
        species=9606 表示人类
        """
        params = {
            "identifiers": "\r".join(protein_ids),
            "species": species,
            "required_score": 700,  # 高置信度 >700
            "caller_identity": "protein_kg_platform"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tsv/network",
            data=params
        )
        
        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            data = [line.split("\t") for line in lines[1:]]  # 跳过表头
            df = pd.DataFrame(data, columns=lines[0].split("\t"))
            print(f"✅ STRING: 获取了 {len(df)} 条相互作用")
            return df
        return pd.DataFrame()
    
    def get_enrichment(self, protein_ids: List[str]) -> Dict:
        """获取功能富集分析"""
        params = {
            "identifiers": "\r".join(protein_ids),
            "species": 9606,
            "caller_identity": "protein_kg_platform"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tsv/enrichment",
            data=params
        )
        
        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            data = [line.split("\t") for line in lines[1:]]
            return {
                "GO_terms": [d for d in data if "GO:" in d[0]][:10],
                "KEGG_pathways": [d for d in data if "KEGG" in d[0]][:5],
                "total_terms": len(data)
            }
        return {}
    
    def resolve_to_string_id(self, protein_ids: List[str]) -> Dict:
        """将 UniProt ID 映射到 STRING ID"""
        params = {
            "identifiers": "\r".join(protein_ids),
            "species": 9606,
            "limit": 1,
            "caller_identity": "protein_kg_platform"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/tsv/resolve",
            data=params
        )
        
        mapping = {}
        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) >= 2:
                    mapping[parts[0]] = parts[1]
        return mapping


if __name__ == "__main__":
    loader = STRINGLoader()
    
    print("🔬 从 STRING 数据库加载蛋白质相互作用...")
    print("="*50)
    
    # P53, BRCA1, EGFR 的 UniProt ID
    proteins = ["P04637", "P38398", "P00533"]
    
    # 1. 获取相互作用网络
    ppi = loader.get_ppi_network(proteins)
    if not ppi.empty:
        print(f"\n📊 高置信度相互作用 (score > 700):")
        for _, row in ppi.iterrows():
            print(f"  {row['preferredName_A']} ↔ {row['preferredName_B']} (score: {row['score']})")
    
    # 2. 功能富集
    enrichment = loader.get_enrichment(proteins)
    if enrichment:
        print(f"\n🧬 功能富集分析 (共 {enrichment['total_terms']} 条):")
        for term in enrichment["GO_terms"][:5]:
            print(f"  GO: {term[1]} ({term[2]} genes)")
        for pathway in enrichment["KEGG_pathways"][:3]:
            print(f"  KEGG: {pathway[1]} ({pathway[2]} genes)")