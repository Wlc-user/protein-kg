import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.etl_integrated import IntegratedETLPipeline
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
PROTEINS_JSON = os.path.join(BASE, 'data', 'all_proteins.json')
KG_EXPORT = os.path.join(BASE, 'data', 'kg_full_export.json')

if not os.path.exists(PROTEINS_JSON):
    print('❗ 请先运行 parse_now.py 生成 all_proteins.json')
    sys.exit(1)

print('🧬 构建知识图谱...')
integrated = IntegratedETLPipeline(ner_mode='simple')
integrated.run_from_existing_data(PROTEINS_JSON)
integrated.export_kg(KG_EXPORT)
stats = integrated.kg_storage.get_stats()
print(f'📊 节点 {stats['total_nodes']} 个, 关系 {stats['total_relations']} 条')

print('📤 导入 Neo4j...')
subprocess.run([sys.executable, 'import_to_neo4j.py'], check=True)
print('✅ 全量知识图谱已导入 Neo4j！')
