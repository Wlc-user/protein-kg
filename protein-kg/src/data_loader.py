"""
蛋白质数据加载器：从 UniProt/PDB 拉取真实数据
"""
import requests
import time
from typing import Dict, List, Optional

class ProteinDataLoader:
    """从 UniProt REST API 加载蛋白质数据"""
    
    BASE_URL = "https://rest.uniprot.org/uniprotkb"
    
    def __init__(self):
        self.cache = {}
    
    def fetch_protein(self, protein_id: str) -> Optional[Dict]:
        """获取单个蛋白质的完整元数据"""
        if protein_id in self.cache:
            return self.cache[protein_id]
        
        url = f"{self.BASE_URL}/{protein_id}.json"
        response = requests.get(url, headers={"Accept": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            result = {
                "id": protein_id,
                "name": data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", ""),
                "gene": self._extract_gene(data),
                "organism": data.get("organism", {}).get("scientificName", ""),
                "sequence": data.get("sequence", {}).get("value", ""),
                "length": data.get("sequence", {}).get("length", 0),
                "function": self._extract_function(data),
                "subcellular_location": self._extract_location(data),
                "interactors": self._extract_interactors(data),
            }
            self.cache[protein_id] = result
            time.sleep(0.2)  # UniProt 限速
            return result
        return None
    
    def fetch_batch(self, protein_ids: List[str]) -> List[Dict]:
        """批量获取蛋白质数据"""
        results = []
        for pid in protein_ids:
            data = self.fetch_protein(pid)
            if data:
                results.append(data)
                print(f"  ✅ {pid}: {data['name'][:50]}")
            else:
                print(f"  ❌ {pid}: 未找到")
        return results
    
    def search_by_keyword(self, keyword: str, limit: int = 10) -> List[str]:
        """按关键词搜索蛋白质ID"""
        url = f"{self.BASE_URL}/search?query={keyword}&size={limit}"
        response = requests.get(url, headers={"Accept": "application/json"})
        if response.status_code == 200:
            results = response.json().get("results", [])
            return [r["primaryAccession"] for r in results]
        return []
    
    def _extract_gene(self, data: Dict) -> str:
        try:
            return data["genes"][0]["geneName"]["value"]
        except (KeyError, IndexError):
            return ""
    
    def _extract_function(self, data: Dict) -> List[str]:
        comments = data.get("comments", [])
        for c in comments:
            if c["commentType"] == "FUNCTION":
                return c.get("texts", [{}])[0].get("value", "").split(". ")
        return []
    
    def _extract_location(self, data: Dict) -> List[str]:
        comments = data.get("comments", [])
        for c in comments:
            if c["commentType"] == "SUBCELLULAR_LOCATION":
                return [loc["location"]["locationValue"] for loc in c.get("subcellularLocations", [])]
        return []
    
    def _extract_interactors(self, data: Dict) -> List[Dict]:
        comments = data.get("comments", [])
        interactors = []
        for c in comments:
            if c["commentType"] == "INTERACTION":
                for interaction in c.get("interactions", []):
                    interactors.append({
                        "partner": interaction.get("interactantOne", {}).get("uniProtkbId", ""),
                        "type": interaction.get("type", "")
                    })
        return interactors


if __name__ == "__main__":
    loader = ProteinDataLoader()
    
    # 测试：加载真实蛋白质
    print("🔬 加载示例蛋白质数据...")
    
    # P53、BRCA1、EGFR 是著名的癌症相关蛋白
    example_proteins = ["P04637", "P38398", "P00533"]
    
    for pid in example_proteins:
        data = loader.fetch_protein(pid)
        if data:
            print(f"\n{'='*50}")
            print(f"蛋白质: {pid}")
            print(f"名称: {data['name']}")
            print(f"基因: {data['gene']}")
            print(f"物种: {data['organism']}")
            print(f"序列长度: {data['length']}")
            print(f"序列(前50): {data['sequence'][:50]}...")