"""
运行完整知识图谱构建 - 处理真实数据
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.etl_integrated import IntegratedETLPipeline
import json

print("=" * 60)
print("蛋白质知识图谱 - 完整构建")
print("=" * 60)

# 初始化
integrated = IntegratedETLPipeline(ner_mode="simple")

# 使用测试数据
test_proteins = [
    {
        "id": "P38398",
        "name": "BRCA1", 
        "function": "BRCA1 is a tumor suppressor that interacts with TP53 and regulates DNA repair in breast cancer."
    },
    {
        "id": "P04637",
        "name": "TP53",
        "function": "TP53 functions as a transcription factor that activates genes involved in cell cycle arrest."
    },
    {
        "id": "P00533",
        "name": "EGFR",
        "function": "EGFR mutations are common in non-small cell lung cancer and promote cell proliferation."
    },
    {
        "id": "P01116",
        "name": "KRAS",
        "function": "KRAS mutations occur in pancreatic cancer and activate downstream signaling pathways."
    },
    {
        "id": "P04626",
        "name": "ERBB2",
        "function": "HER2 amplification is associated with aggressive breast cancer and poor prognosis."
    }
]

os.makedirs("data", exist_ok=True)
with open("data/test_proteins.json", "w", encoding='utf-8') as f:
    json.dump(test_proteins, f, ensure_ascii=False, indent=2)

# 处理数据
result = integrated.run_from_existing_data("data/test_proteins.json")

# 查询示例
print("\n" + "=" * 60)
print("🔍 知识图谱查询示例")
print("=" * 60)

test_entities = ["BRCA1", "TP53", "EGFR", "KRAS", "ERBB2"]
for entity in test_entities:
    results = integrated.query_kg(entity)
    if results:
        print(f"\n'{entity}' 的关联:")
        for r in results[:5]:
            direction = "→" if r['direction'] == 'outgoing' else "←"
            print(f"   {direction} {r['related_name']} ({r['relation']})")

# 导出完整知识图谱
integrated.export_kg("data/kg_full_export.json")

# 显示统计
stats = integrated.kg_storage.get_stats()
print("\n" + "=" * 60)
print("📊 最终统计")
print("=" * 60)
print(f"  总节点数: {stats['total_nodes']}")
print(f"  总关系数: {stats['total_relations']}")
print(f"  节点类型: {stats['node_types']}")

print("\n✅ 完成！知识图谱已保存到 data/kg_data/ 目录")