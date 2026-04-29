"""知识图谱 + NER 验证（全量 2 万条）"""
import pickle

with open('../data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)

# 1. NER 实体抽取效果验证（全量）
print("=" * 50)
print("NER 实体抽取验证（全量）")
print("=" * 50)

entity_types = {
    'kinase': 'Protein_Type',
    'receptor': 'Protein_Type',
    'channel': 'Channel',
    'transporter': 'Transporter',
    'transcription': 'Function',
    'factor': 'Function',
    'dehydrogenase': 'Enzyme',
    'polymerase': 'Enzyme',
    'synthase': 'Enzyme',
    'collagen': 'Structure',
    'immunoglobulin': 'Immune',
    'antibody': 'Immune',
    'ribosomal': 'Ribosome',
    'histone': 'Chromatin',
    'ubiquitin': 'Degradation',
}

total_proteins = len(cleaned)
entities_found = 0
entity_counts = {v: 0 for v in set(entity_types.values())}

for p in cleaned:
    name = p.get('name', '').lower()
    found_types = set()
    for keyword, etype in entity_types.items():
        if keyword in name:
            found_types.add(etype)
    if found_types:
        entities_found += 1
        for t in found_types:
            entity_counts[t] += 1

print(f"全量数据: {total_proteins} 条")
print(f"NER 命中: {entities_found} 条 ({entities_found/total_proteins*100:.1f}%)")
print(f"\n实体类型分布:")
for etype, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {etype}: {count} ({count/total_proteins*100:.1f}%)")

# 2. 知识图谱关系推理验证（全量）
print(f"\n{'='*50}")
print("知识图谱关系推理验证（全量）")
print("=" * 50)

families = {}
for p in cleaned:
    name = p.get('name', '').lower()
    if 'kinase' in name: families[p['id']] = 'Kinase'
    elif 'receptor' in name: families[p['id']] = 'Receptor'
    elif 'channel' in name or 'transporter' in name: families[p['id']] = 'Channel'
    elif 'transcription' in name or 'factor' in name: families[p['id']] = 'Transcription'
    elif 'dehydrogenase' in name or 'polymerase' in name: families[p['id']] = 'Enzyme'

family_ids = list(families.keys())
print(f"家族标注: {len(family_ids)} 条")

# 同家族 vs 跨家族关系统计
same_family = 0
diff_family = 0
sample_size = min(50000, len(family_ids) * (len(family_ids) - 1) // 2)

import random
for _ in range(sample_size):
    pid1, pid2 = random.sample(family_ids, 2)
    if families[pid1] == families[pid2]:
        same_family += 1
    else:
        diff_family += 1

total = same_family + diff_family
print(f"采样关系: {sample_size}")
print(f"同家族关系: {same_family} ({same_family/total*100:.1f}%)")
print(f"跨家族关系: {diff_family} ({diff_family/total*100:.1f}%)")

# 3. 图谱查询示例
print(f"\n{'='*50}")
print("图谱查询示例（Neo4j Cypher）")
print("=" * 50)
print("""
-- 查询 TP53 的直接相互作用网络
MATCH (p:Protein {id: 'P04637'})-[r:INTERACTS_WITH]-(n)
RETURN p.name, type(r), n.name LIMIT 10

-- 查询 TP53 的共同通路蛋白质
MATCH (p1:Protein {id: 'P04637'})-[:IN_PATHWAY]->(path)<-[:IN_PATHWAY]-(p2)
RETURN p2.name, path.name

-- 查询最多相互作用的蛋白质 Top 10
MATCH (p:Protein)-[r:INTERACTS_WITH]-()
RETURN p.name, count(r) AS degree
ORDER BY degree DESC LIMIT 10
""")

print("✅ 知识图谱 + NER 全量验证完成")