"""
整合ETL流水线和知识图谱
在数据清洗后自动进行NER提取并存入知识图谱
"""
import json
import os
from typing import List, Dict

# 正确的导入路径
from src.data_loader import ProteinDataLoader
from src.local_loader import LocalProteinLoader
from src.data_cleaner import ProteinDataCleaner
from src.ner_extractor import get_ner
from src.file_storage import FileStorage


class IntegratedETLPipeline:
    """
    整合ETL + NER + 知识图谱的完整流水线
    """
    
    def __init__(self, ner_mode: str = "simple"):
        self.ner = get_ner(ner_mode)
        self.kg_storage = FileStorage()
        
        self.stats = {
            "total_proteins": 0,
            "total_entities": 0,
            "total_relations": 0,
            "proteins_with_entities": 0
        }
    
    def _extract_from_function(self, function_text: str, protein_name: str) -> Dict:
        """从蛋白质功能描述中提取实体和关系"""
        if not function_text or len(function_text) < 10:
            return {"entities": [], "relations": []}
        
        entities = self.ner.extract_with_positions(function_text)
        relations = self.ner.extract_relations(function_text)
        
        # 添加蛋白质本身到实体的关系
        for ent in entities:
            relations.append((protein_name, "has_function", ent[0]))
        
        return {"entities": entities, "relations": relations}
    
    def process_protein_batch(self, proteins: List[Dict], source: str = "UniProt") -> List[Dict]:
        """批量处理蛋白质"""
        results = []
        
        for i, protein in enumerate(proteins):
            protein_id = protein.get('id', 'unknown')
            protein_name = protein.get('name', protein_id)
            function = protein.get('function', '')
            
            print(f"\n[{i+1}/{len(proteins)}] 处理: {protein_name}")
            
            extraction = self._extract_from_function(function, protein_name)
            
            if extraction['entities'] or extraction['relations']:
                self.kg_storage.add_entities_and_relations(
                    extraction['entities'],
                    extraction['relations']
                )
                self.stats['proteins_with_entities'] += 1
            
            self.stats['total_entities'] += len(extraction['entities'])
            self.stats['total_relations'] += len(extraction['relations'])
            
            results.append({
                "protein_id": protein_id,
                "protein_name": protein_name,
                "entity_count": len(extraction['entities']),
                "relation_count": len(extraction['relations'])
            })
        
        return results
    
    def run_from_existing_data(self, data_path: str, limit: int = None) -> Dict:
        """从已有的ETL输出文件加载数据并构建知识图谱"""
        print("=" * 60)
        print("🔬 从已有数据构建知识图谱")
        print("=" * 60)
        
        if not os.path.exists(data_path):
            print(f"❌ 文件不存在: {data_path}")
            return {}
        
        with open(data_path, 'r', encoding='utf-8') as f:
            proteins = json.load(f)
        
        if limit:
            proteins = proteins[:limit]
        
        print(f"📥 加载了 {len(proteins)} 个蛋白质")
        
        results = self.process_protein_batch(proteins, "Existing")
        self.stats['total_proteins'] = len(proteins)
        self._print_summary()
        
        return {"processed_proteins": results, "stats": self.stats}
    
    def _print_summary(self):
        """打印汇总统计"""
        print("\n" + "=" * 60)
        print("📊 知识图谱构建完成!")
        print("=" * 60)
        print(f"   📦 蛋白质总数: {self.stats['total_proteins']}")
        print(f"   🧬 含实体的蛋白质: {self.stats['proteins_with_entities']}")
        print(f"   🔍 提取实体数: {self.stats['total_entities']}")
        print(f"   🔗 提取关系数: {self.stats['total_relations']}")
        
        kg_stats = self.kg_storage.get_stats()
        print(f"\n   💾 知识图谱存储状态:")
        print(f"      节点数: {kg_stats['total_nodes']}")
        print(f"      关系数: {kg_stats['total_relations']}")
    
    def query_kg(self, entity_name: str):
        """查询知识图谱"""
        return self.kg_storage.query(entity_name)
    
    def export_kg(self, output_path: str = "data/kg_complete_export.json"):
        """导出完整知识图谱"""
        nodes_data = self.kg_storage._load_nodes()
        relations = self.kg_storage._load_relations()
        
        export_data = {
            "metadata": {
                "source": "Protein ETL Pipeline",
                "total_proteins": self.stats['total_proteins'],
                "total_entities": self.stats['total_entities'],
                "total_relations": self.stats['total_relations']
            },
            "nodes": nodes_data["nodes"],
            "relations": relations
        }
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 知识图谱已导出到: {output_path}")
        return output_path


if __name__ == "__main__":
    pipeline = IntegratedETLPipeline(ner_mode="simple")
    
    test_proteins = [
        {"id": "P38398", "name": "BRCA1", "function": "BRCA1 interacts with TP53 in breast cancer."},
        {"id": "P04637", "name": "TP53", "function": "TP53 is a tumor suppressor."}
    ]
    
    os.makedirs("data", exist_ok=True)
    with open("data/test.json", "w") as f:
        json.dump(test_proteins, f)
    
    pipeline.run_from_existing_data("data/test.json")
    print(pipeline.query_kg("BRCA1"))
