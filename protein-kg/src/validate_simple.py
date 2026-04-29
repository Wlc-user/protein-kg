"""
自己验证自己：把已知蛋白质家族作为 ground truth
如果输入 EGFR 序列，返回的 Top 10 里有 8 个是激酶家族 → 准确率 80%
"""
import pickle, numpy as np
from collections import defaultdict

with open('data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)

# 1. 按名称中的关键词分组（作为 ground truth）
families = defaultdict(list)
for p in cleaned:
    name = p.get('name', '').lower()
    if 'kinase' in name: families['Kinase'].append(p['id'])
    if 'receptor' in name: families['Receptor'].append(p['id'])
    if 'channel' in name or 'transporter' in name: families['Channel/Transporter'].append(p['id'])
    if 'transcription' in name or 'factor' in name: families['Transcription'].append(p['id'])
    if 'dehydrogenase' in name or 'polymerase' in name or 'synthase' in name: families['Enzyme'].append(p['id'])
    if 'collagen' in name: families['Collagen'].append(p['id'])
    if 'immunoglobulin' in name or 'antibody' in name:
        families['Immunoglobulin'].append(p['id'])

print(f"Ground Truth 家族: {dict((k, len(v)) for k, v in families.items())}")
# 2. 对每个家族抽样，检索相似蛋白质
from fast_embed import FastEmbeddingService
service = FastEmbeddingService(concurrency=50)
service.build_index([p for p in cleaned if p['id'] in sum([v for v in families.values()], [])], batch_size=5000)

accuracies = {}
for family, ids in families.items():
    if len(ids) < 5:
        continue
    correct = 0
    total = 0
    for pid in ids[:10]:  # 每个家族取 10 个做查询
        p = next((x for x in cleaned if x['id'] == pid), None)
        if not p:
            continue
        from protein_recommender import ProteinRecommender
        rec = ProteinRecommender()
       
        from multi_recall import ProteinMultiRecall
        multi = ProteinMultiRecall(rec)
        results = multi.recall(p['sequence'], query_func=p.get('name', ''), topk=10)
        result_ids = [r[0] if isinstance(r, tuple) else r['protein_id'] for r in results if (r[0] if isinstance(r, tuple) else r['protein_id']) != pid]
        # 命中同一家族的算正确
        correct += sum(1 for rid in result_ids if rid in ids)
        total += len(result_ids)
    accuracies[family] = correct / total if total > 0 else 0

print("\n家族内检索准确率:")
for family, acc in accuracies.items():
    print(f"  {family}: {acc:.1%}")
print(f"  平均: {np.mean(list(accuracies.values())):.1%}")
