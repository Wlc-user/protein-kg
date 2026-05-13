"""
文件存储 - 将实体和关系保存为JSON文件
无需安装Neo4j即可使用
"""
import json
import os
from typing import List, Dict, Tuple
from datetime import datetime

class FileStorage:
    def __init__(self, data_dir: str = "E:/pyspace/protein-kg/data/kg_data"):
        self.data_dir = data_dir
        self.nodes_file = os.path.join(data_dir, "nodes.json")
        self.relations_file = os.path.join(data_dir, "relations.json")
        self._ensure_dir()
    
    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_nodes(self) -> Dict:
        """加载节点数据"""
        if os.path.exists(self.nodes_file):
            with open(self.nodes_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"nodes": [], "last_id": 0}
    
    def _load_relations(self) -> List:
        """加载关系数据"""
        if os.path.exists(self.relations_file):
            with open(self.relations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_nodes(self, data: Dict):
        """保存节点数据"""
        with open(self.nodes_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_relations(self, data: List):
        """保存关系数据"""
        with open(self.relations_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_node(self, name: str, node_type: str):
        """添加节点"""
        nodes_data = self._load_nodes()
        
        # 检查是否已存在
        for node in nodes_data["nodes"]:
            if node["name"] == name and node["type"] == node_type:
                return node["id"]
        
        # 新增节点
        nodes_data["last_id"] += 1
        new_node = {
            "id": nodes_data["last_id"],
            "name": name,
            "type": node_type,
            "created_at": datetime.now().isoformat()
        }
        nodes_data["nodes"].append(new_node)
        self._save_nodes(nodes_data)
        return new_node["id"]
    
    def add_relation(self, source_name: str, target_name: str, rel_type: str):
        """添加关系"""
        relations = self._load_relations()
        
        # 检查是否已存在相同关系
        for rel in relations:
            if (rel["source"] == source_name and 
                rel["target"] == target_name and 
                rel["type"] == rel_type):
                return
        
        relations.append({
            "source": source_name,
            "target": target_name,
            "type": rel_type,
            "created_at": datetime.now().isoformat()
        })
        self._save_relations(relations)
    
    def add_entities_and_relations(self, entities: List[Tuple], relations: List[Tuple]):
        """批量添加实体和关系"""
        # 添加实体节点
        for name, node_type, _, _ in entities:
            self.add_node(name, node_type)
        
        # 添加关系
        for source, rel_type, target in relations:
            self.add_relation(source, target, rel_type)
        
        print(f"✅ 已添加 {len(entities)} 个实体, {len(relations)} 个关系")
    
    def query(self, entity_name: str) -> List[Dict]:
        """查询实体的关联关系"""
        relations = self._load_relations()
        results = []
        
        for rel in relations:
            if rel["source"] == entity_name:
                results.append({
                    "related_name": rel["target"],
                    "relation": rel["type"],
                    "direction": "outgoing"
                })
            elif rel["target"] == entity_name:
                results.append({
                    "related_name": rel["source"],
                    "relation": rel["type"],
                    "direction": "incoming"
                })
        
        return results
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        nodes_data = self._load_nodes()
        relations = self._load_relations()
        
        return {
            "total_nodes": len(nodes_data["nodes"]),
            "total_relations": len(relations),
            "node_types": self._count_node_types(nodes_data["nodes"])
        }
    
    def _count_node_types(self, nodes: List) -> List:
        """统计节点类型分布"""
        type_count = {}
        for node in nodes:
            t = node["type"]
            type_count[t] = type_count.get(t, 0) + 1
        return [{"type": k, "count": v} for k, v in type_count.items()]
    
    def clear_all(self):
        """清空所有数据"""
        if os.path.exists(self.nodes_file):
            os.remove(self.nodes_file)
        if os.path.exists(self.relations_file):
            os.remove(self.relations_file)
        print("✅ 已清空所有数据")


if __name__ == '__main__':
    # 测试
    storage = FileStorage()
    storage.clear_all()
    
    # 添加测试数据
    entities = [("BRCA1", "PROTEIN", 0, 0), ("TP53", "PROTEIN", 0, 0)]
    relations = [("BRCA1", "interacts_with", "TP53")]
    
    storage.add_entities_and_relations(entities, relations)
    
    # 查询
    results = storage.query("BRCA1")
    print("查询 BRCA1:", results)
    
    # 统计
    stats = storage.get_stats()
    print("统计:", stats)