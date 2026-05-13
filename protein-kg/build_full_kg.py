import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.etl_integrated import IntegratedETLPipeline
import subprocess

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROTEINS_JSON = os.path.join(BASE_DIR, "data", "all_proteins.json")
KG_EXPORT = os.path.join(BASE_DIR, "data", "kg_full_export.json")

print("🧬 从本地 JSON 构建知识图谱...")
if not os.path.exists(PROTEINS_JSON):
    print(f"❌ 未找到 {PROTEINS_JSON}，请先运行 parse_uniprot_v2.py 生成该文件。")
    sys.exit(1)

integrated = IntegratedETLPipeline(ner_mode="simple")
result = integrated.run_from_existing_data(PROTEINS_JSON)
integrated.export_kg(KG_EXPORT)
stats = integrated.kg_storage.get_stats()
print(f"📊 知识图谱统计: 节点 {stats['total_nodes']} 个, 关系 {stats['total_relations']} 条")
print(f"💾 已导出至 {KG_EXPORT}")

print("\n📤 导入 Neo4j...")
subprocess.run([sys.executable, "import_to_neo4j.py"], check=True)
print("✅ 全量知识图谱已成功导入 Neo4j！")