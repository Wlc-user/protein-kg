"""
知识图谱构建器 - 整合NER和Neo4j存储
"""
from typing import List, Dict, Optional
from .ner_extractor import get_ner
from .kg_storage import Neo4jKG
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    def __init__(self, ner_mode: str = "biobert", neo4j_uri: str = "bolt://localhost:7687"):
        """
        初始化图谱构建器
        
        参数:
            ner_mode: "biobert" 或 "simple"
            neo4j_uri: Neo4j连接地址
        """
        self.ner = get_ner(ner_mode)
        self.kg = Neo4jKG(uri=neo4j_uri)
        self.kg_connected = False
    
    def connect(self):
        """连接到Neo4j"""
        self.kg_connected = self.kg.connect()
        if not self.kg_connected:
            logger.warning("Neo4j未连接，数据将只打印不存储")
        return self.kg_connected
    
    def process_text(self, text: str, source_id: str = "unknown", store: bool = True) -> Dict:
        """
        处理单条文本，提取实体关系并存储
        
        参数:
            text: 输入文本
            source_id: 数据来源标识
            store: 是否存储到Neo4j
        
        返回: 提取结果统计
        """
        logger.info(f"处理文本 [{source_id}]: {text[:100]}...")
        
        # 提取实体
        entities = self.ner.extract_with_positions(text)
        logger.info(f"  提取到 {len(entities)} 个实体")
        
        # 提取关系
        relations = self.ner.extract_relations(text)
        logger.info(f"  提取到 {len(relations)} 个关系")
        
        # 存储到Neo4j
        if store and self.kg_connected:
            for ent in entities:
                self.kg.create_node(ent[0], ent[1])
            for rel in relations:
                self.kg.create_relation(rel[0], rel[2], rel[1])
        
        return {
            "source_id": source_id,
            "entities": [(e[0], e[1]) for e in entities],
            "relations": relations,
            "entity_count": len(entities),
            "relation_count": len(relations)
        }
    
    def process_batch(self, texts: List[Dict], store: bool = True) -> List[Dict]:
        """
        批量处理文本
        
        参数:
            texts: 文本列表，每个元素含 {"id": "...", "text": "..."}
            store: 是否存储
        
        返回: 所有结果列表
        """
        results = []
        for item in texts:
            result = self.process_text(
                text=item.get("text", ""),
                source_id=item.get("id", "unknown"),
                store=store
            )
            results.append(result)
        
        # 打印汇总
        total_entities = sum(r["entity_count"] for r in results)
        total_relations = sum(r["relation_count"] for r in results)
        logger.info("=" * 50)
        logger.info(f"批量处理完成:")
        logger.info(f"  文本数: {len(results)}")
        logger.info(f"  实体总数: {total_entities}")
        logger.info(f"  关系总数: {total_relations}")
        
        return results
    
    def query(self, entity_name: str, depth: int = 2) -> List[Dict]:
        """查询实体的关联网络"""
        if not self.kg_connected:
            logger.error("Neo4j未连接，无法查询")
            return []
        return self.kg.query_protein_network(entity_name, depth)
    
    def get_stats(self) -> Dict:
        """获取图谱统计信息"""
        if not self.kg_connected:
            return {}
        return self.kg.get_stats()
    
    def close(self):
        """关闭连接"""
        if self.kg_connected:
            self.kg.close()


if __name__ == '__main__':
    # 测试
    builder = KnowledgeGraphBuilder(ner_mode="simple")  # 先用simple模式测试
    builder.connect()
    
    test_texts = [
        {"id": "test1", "text": "BRCA1 interacts with TP53 in breast cancer."},
        {"id": "test2", "text": "EGFR mutations cause lung cancer."}
    ]
    
    results = builder.process_batch(test_texts, store=True)
    print("\n处理结果:")
    for r in results:
        print(f"  {r['source_id']}: {r['entity_count']} 实体, {r['relation_count']} 关系")
    
    if builder.kg_connected:
        stats = builder.get_stats()
        print(f"\n图谱统计: {stats}")
    
    builder.close()