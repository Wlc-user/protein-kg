import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "protein123")

def create_constraints(tx):
    tx.run("CREATE CONSTRAINT entity_unique IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE")

def import_graph(json_path):
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)

    driver = GraphDatabase.driver(URI, auth=AUTH)
    with driver.session() as session:
        session.execute_write(create_constraints)

        # 导入节点
        for node in data["nodes"]:
            label = node["type"]
            name = node["id"]
            props = node.get("properties", {})
            session.run(
                f"MERGE (n:{label} {{name: $name}}) SET n += $props",
                name=name, props=props
            )

        # 导入关系（使用 relations 键）
        for rel in data["relations"]:
            src = rel["source"]
            tgt = rel["target"]
            rel_type = rel["type"].replace("-", "_").replace(" ", "_").replace(".", "_").upper()
            session.run(
                f"MATCH (a {{name: $src}}) MATCH (b {{name: $tgt}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) RETURN count(r)",
                src=src, tgt=tgt
            )

    driver.close()
    print("✅ 导入 Neo4j 完成！")

if __name__ == "__main__":
    import_graph("data/kg_full_export.json")