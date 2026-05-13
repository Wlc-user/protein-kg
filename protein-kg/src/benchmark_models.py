"""ESM-2 检索效果验证"""
import pickle, numpy as np, time
from collections import defaultdict
import sys
sys.path.insert(0, '.')
from fast_embed import FastEmbeddingService

with open('../data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)

families = defaultdict(list)
for p in cleaned:
    name = p.get('name', '').lower()
    if 'kinase' in name: families['Kinase'].append(p['id'])
    if 'receptor' in name: families['Receptor'].append(p['id'])
    if 'channel' in name or 'transporter' in name: families['Channel'].append(p['id'])
    if 'transcription' in name or 'factor' in name: families['Transcription'].append(p['id'])
    if 'dehydrogenase' in name or 'polymerase' in name: families['Enzyme'].append(p['id'])
    if 'collagen' in name: families['Collagen'].append(p['id'])
    if 'immunoglobulin' in name or 'antibody' in name: families['Immunoglobulin'].append(p['id'])

all_ids = set()
for v in families.values(): all_ids.update(v)
family_proteins = [p for p in cleaned if p['id'] in all_ids]

print(f"Proteins: {len(family_proteins)}, Families: {len(families)}")

service = FastEmbeddingService(concurrency=50)
service.build_index(family_proteins, batch_size=5000)

accuracies = {}
for family, ids in families.items():
    if len(ids) < 5: continue
    correct, total = 0, 0
    for pid in ids[:15]:
        p = next((x for x in cleaned if x['id'] == pid), None)
        if not p: continue
        results = service.search(p['sequence'], top_k=10)
        for r in results:
            if r['protein_id'] != pid and r['protein_id'] in ids:
                correct += 1
            total += 1
    if total > 0:
        accuracies[family] = correct / total
        print(f"  {family}: {accuracies[family]:.1%}")

print(f"Average: {np.mean(list(accuracies.values())):.1%}")