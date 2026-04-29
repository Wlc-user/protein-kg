"""
蛋白质知识图谱构建器：Neo4j 存储 + Cypher 查询
"""
from neo4j import GraphDatabase
from typing import Dict, List
import json

class ProteinGraphBuilder:
    """将蛋白质数据存入 Neo4j 图数据库"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self._init_indexes()
    
    def _init_indexes(self):
        """创建索引加速查询"""
        with self.driver.session() as session:
            session.run("CREATE INDEX IF NOT EXISTS FOR (p:Protein) ON (p.id)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (g:Gene) ON (g.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (o:Organism) ON (o.name)")
    
    def import_protein(self, protein_data: Dict):
        """导入单个蛋白质及其关系"""
        with self.driver.session() as session:
            # 创建蛋白质节点
            session.run("""
                MERGE (p:Protein {id: $id})
                SET p.name = $name,
                    p.sequence = $sequence,
                    p.length = $length,
                    p.function = $function
            """, 
                id=protein_data["id"],
                name=protein_data["name"],
                sequence=protein_data.get("sequence", ""),
                length=protein_data.get("length", 0),
                function="; ".join(protein_data.get("function", []))[:1000]
            )
            
            # 创建基因节点和关系
            if protein_data.get("gene"):
                session.run("""
                    MATCH (p:Protein {id: $pid})
                    MERGE (g:Gene {name: $gene})
                    MERGE (p)-[:ENCODED_BY]->(g)
                """, pid=protein_data["id"], gene=protein_data["gene"])
            
            # 创建物种节点和关系
            if protein_data.get("organism"):
                session.run("""
                    MATCH (p:Protein {id: $pid})
                    MERGE (o:Organism {name: $org})
                    MERGE (p)-[:FROM_ORGANISM]->(o)
                """, pid=protein_data["id"], org=protein_data["organism"])
            
            # 创建亚细胞定位关系
            for loc in protein_data.get("subcellular_location", []):
                session.run("""
                    MATCH (p:Protein {id: $pid})
                    MERGE (l:Location {name: $loc})
                    MERGE (p)-[:LOCATED_IN]->(l)
                """, pid=protein_data["id"], loc=loc)
            
            # 创建蛋白质相互作用关系
            for interactor in protein_data.get("interactors", []):
                partner_id = interactor.get("partner")
                if partner_id:
                    session.run("""
                        MATCH (p1:Protein {id: $pid})
                        MERGE (p2:Protein {id: $partner})
                        MERGE (p1)-[:INTERACTS_WITH {type: $itype}]->(p2)
                    """, pid=protein_data["id"], partner=partner_id, itype=interactor.get("type", "unknown"))
    
    def import_batch(self, proteins: List[Dict]):
        """批量导入蛋白质数据"""
        for i, protein in enumerate(proteins):
            try:
                self.import_protein(protein)
                print(f"  ✅ [{i+1}/{len(proteins)}] {protein['id']}: {protein['name'][:40]}")
            except Exception as e:
                print(f"  ❌ [{i+1}/{len(proteins)}] {protein['id']}: {e}")
    
    def query_ppi_network(self, protein_id: str, depth: int = 1) -> List[Dict]:
        """查询蛋白质相互作用网络"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Protein {id: $id})-[r:INTERACTS_WITH]-(neighbor:Protein)
                RETURN p.id AS source, p.name AS source_name, 
                       type(r) AS relation, r.type AS detail,
                       neighbor.id AS target, neighbor.name AS target_name
                LIMIT 50
            """, id=protein_id)
            return [record.data() for record in result]
    
    def query_by_function(self, keyword: str) -> List[Dict]:
        """按功能搜索蛋白质"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Protein)
                WHERE p.function CONTAINS $keyword
                RETURN p.id AS id, p.name AS name, p.function AS function
                LIMIT 20
            """, keyword=keyword)
            return [record.data() for record in result]
    
    def get_statistics(self) -> Dict:
        """获取图谱统计信息"""
        with self.driver.session() as session:
            proteins = session.run("MATCH (p:Protein) RETURN count(p) AS cnt").single()["cnt"]
            genes = session.run("MATCH (g:Gene) RETURN count(g) AS cnt").single()["cnt"]
            interactions = session.run("MATCH ()-[r:INTERACTS_WITH]->() RETURN count(r) AS cnt").single()["cnt"]
            return {
                "total_proteins": proteins,
                "total_genes": genes,
                "total_interactions": interactions
            }
    
    def close(self):
        self.driver.close()


if __name__ == "__main__":
    from data_loader import ProteinDataLoader
    
    print("🔬 蛋白质知识图谱构建演示")
    print("="*50)
    
    # 1. 加载真实蛋白质数据
    loader = ProteinDataLoader()
    proteins = loader.fetch_batch(["P04637", "P38398", "P00533"])
    
    # 2. 导入 Neo4j
    print("\n📊 导入 Neo4j 图数据库...")
    builder = ProteinGraphBuilder(uri="bolt://localhost:7687", user="neo4j", password="password")
    builder.import_batch(proteins)
    
    # 3. 查询统计
    stats = builder.get_statistics()
    print(f"\n📈 图谱统计: {json.dumps(stats, indent=2)}")
    
    # 4. 查询 P53 的相互作用网络
    print(f"\n🔗 P53 (P04637) 相互作用网络:")
    network = builder.query_ppi_network("P04637")
    for edge in network[:5]:
        print(f"  {edge['source_name']} → {edge['target_name']}")
    
    builder.close()