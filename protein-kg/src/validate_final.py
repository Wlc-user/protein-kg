"""最终验证：三路召回（序列 + 功能 + 热门）准确率"""
import pickle, numpy as np
from collections import defaultdict
from fast_embed import FastEmbeddingService

with open('../data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)

# 1. Ground Truth
families = defaultdict(list)
for p in cleaned:
    name = p.get('name', '').lower()
    if 'kinase' in name: families['Kinase'].append(p['id'])
    if 'receptor' in name: families['Receptor'].append(p['id'])
    if 'channel' in name or 'transporter' in name: families['Channel'].append(p['id'])
    if 'transcription' in name or 'factor' in name: families['Transcription'].append(p['id'])
    if 'dehydrogenase' in name or 'polymerase' in name or 'synthase' in name: families['Enzyme'].append(p['id'])
    if 'collagen' in name: families['Collagen'].append(p['id'])
    if 'immunoglobulin' in name or 'antibody' in name: families['Immunoglobulin'].append(p['id'])

print("Ground Truth: " + str({k: len(v) for k, v in families.items()}))

# 2. 构建索引
all_ids = set()
for v in families.values(): all_ids.update(v)

protein_map = {p['id']: p for p in cleaned if p['id'] in all_ids}
family_proteins = list(protein_map.values())
print(f"Annotated: {len(family_proteins)} proteins")

service = FastEmbeddingService(concurrency=50)
service.build_index(family_proteins, batch_size=5000)

# 3. 热门蛋白质（长度排序前100）
sorted_proteins = sorted(family_proteins, key=lambda x: x.get('length', 0) or 0, reverse=True)[:100]
hot_ids = {p['id'] for p in sorted_proteins}

# 4. 三路召回验证
def multi_recall(seq, func_name, topk=10):
    """序列 + 功能 + 热门 三路融合"""
    scores = defaultdict(float)
    
    # 路1：序列相似（Faiss）
    seq_results = service.search(seq, top_k=topk * 3)
    for r in seq_results:
        scores[r['protein_id']] += r['similarity'] * 0.5
    
    # 路2：功能关键词匹配
    for pid in all_ids:
        name = protein_map.get(pid, {}).get('name', '').lower()
        for word in func_name.lower().split():
            if word in name:
                scores[pid] += 0.3
    
    # 路3：热门兜底
    for pid in hot_ids:
        if pid not in scores:
            scores[pid] += 0.1
    
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [pid for pid, _ in ranked[:topk]]

print("\n--- Multi-Recall Validation ---")
accuracies = {}
for family, ids in families.items():
    if len(ids) < 5: continue
    correct = 0
    total = 0
    for pid in ids[:15]:
        p = protein_map.get(pid)
        if not p: continue
        results = multi_recall(p['sequence'], p.get('name', ''), topk=10)
        results = [r for r in results if r != pid]
        correct += sum(1 for r in results if r in ids)
        total += len(results)
    if total > 0:
        accuracies[family] = correct / total
        print(f"  {family}: {accuracies[family]:.1%}")

if accuracies:
    avg = np.mean(list(accuracies.values()))
    print(f"\nMulti-Recall Average: {avg:.1%}")