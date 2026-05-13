"""
从 UniProt API 获取少量蛋白质的 GO 注释和相互作用，构建示例知识图谱
"""

import json
import requests
import time
from pathlib import Path
from Bio import SeqIO
from tqdm import tqdm
from collections import defaultdict

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FASTA_PATH = DATA_DIR / "human_proteome.fasta"
OUT_JSON = DATA_DIR / "kg_sample_export.json"

# 限制处理的蛋白质数量（改为 200 避免 API 太慢，足够展示）
MAX_PROTEINS = 200

def get_uniprot_ids_from_fasta(limit=MAX_PROTEINS):
    """从 FASTA 文件提取前 limit 个 UniProt ID"""
    ids = []
    for record in SeqIO.parse(FASTA_PATH, "fasta"):
        # FASTA 头部示例：sp|P05067|A4_HUMAN ...
        header = record.id
        if '|' in header:
            uniprot_id = header.split('|')[1]
        else:
            continue
        ids.append(uniprot_id)
        if len(ids) >= limit:
            break
    print(f"提取到 {len(ids)} 个 UniProt ID")
    return ids

def fetch_uniprot_entry(uniprot_id):
    """通过 UniProt REST API 获取单个蛋白质的完整条目（XML 或 JSON）"""
    url = f"https://www.uniprot.org/uniprot/{uniprot_id}.json"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        else:
            return None
    except:
        return None

def parse_go_from_entry(entry):
    """从 JSON 条目中提取 GO 注释（ID 和名称）"""
    go_terms = []
    try:
        for db_ref in entry.get('uniProtKBCrossReferences', []):
            if db_ref.get('database') == 'GO':
                go_id = db_ref.get('id')
                go_name = db_ref.get('properties', {}).get('GO-term')
                if go_id and go_name:
                    # 从 GO ID 推断分类（C, F, P）
                    category_map = {'C': 'CC', 'F': 'MF', 'P': 'BP'}
                    category_code = go_id.split(':')[1][0] if ':' in go_id else ''
                    category = category_map.get(category_code, 'unknown')
                    go_terms.append({
                        'id': go_id,
                        'name': go_name,
                        'category': category
                    })
    except:
        pass
    return go_terms

def parse_ppi_from_entry(entry):
    """从条目中提取相互作用（仅作为示例，实际 PPI 可后续扩展）"""
    # UniProt 的相互作用一般在 "comments" -> "INTERACTION" 部分
    interactions = []
    try:
        comments = entry.get('comments', [])
        for comm in comments:
            if comm.get('type') == 'INTERACTION':
                for interact in comm.get('interactions', []):
                    for partner in interact.get('interactants', []):
                        # 可能包含另一个蛋白质的 ID
                        other_id = partner.get('uniProtKBAccessionId')
                        if other_id and other_id != entry.get('primaryAccession'):
                            interactions.append(other_id)
    except:
        pass
    return interactions

def build_sample_kg():
    uniprot_ids = get_uniprot_ids_from_fasta(MAX_PROTEINS)
    proteins = {}
    go_terms_dict = {}
    protein_go_edges = []   # (protein_id, go_id)
    ppi_edges = []          # (protein1, protein2)

    for uid in tqdm(uniprot_ids, desc="Fetching from UniProt"):
        data = fetch_uniprot_entry(uid)
        if not data:
            continue
        # 记录蛋白质
        proteins[uid] = {
            'id': uid,
            'name': data.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', uid),
            'type': 'PROTEIN'
        }
        # 解析 GO
        go_list = parse_go_from_entry(data)
        for go in go_list:
            go_id = go['id']
            if go_id not in go_terms_dict:
                go_terms_dict[go_id] = {
                    'id': go_id,
                    'name': go['name'],
                    'category': go['category'],
                    'type': 'GoTerm'
                }
            protein_go_edges.append((uid, go_id))
        # 解析 PPI（可选）
        ppi_partners = parse_ppi_from_entry(data)
        for partner in ppi_partners:
            if partner in proteins:   # 只保留已经出现在当前集合内的蛋白质
                ppi_edges.append((uid, partner))
        time.sleep(0.05)  # 避免请求过快

    # 构建 Neo4j 兼容的 JSON 结构
    nodes = []
    node_id_map = {}
    # 分配节点 ID
    for idx, (uid, info) in enumerate(proteins.items(), start=1):
        node_id_map[uid] = idx
        nodes.append({
            'id': idx,
            'name': info['name'],
            'type': info['type'],
            'created_at': '2026-05-11T23:59:59'
        })
    for go_id, info in go_terms_dict.items():
        idx = len(nodes) + 1
        node_id_map[go_id] = idx
        nodes.append({
            'id': idx,
            'name': info['name'],
            'type': info['type'],
            'category': info['category']
        })

    # 构建关系（relations）
    relations = []
    for uid, go_id in protein_go_edges:
        relations.append({
            'from': node_id_map[uid],
            'to': node_id_map[go_id],
            'type': 'has_function'
        })
    for p1, p2 in ppi_edges:
        if p1 in node_id_map and p2 in node_id_map:
            relations.append({
                'from': node_id_map[p1],
                'to': node_id_map[p2],
                'type': 'interacts_with'
            })

    kg = {
        'metadata': {'source': 'UniProt API sample', 'num_proteins': len(proteins), 'num_go': len(go_terms_dict)},
        'nodes': nodes,
        'relations': relations
    }

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2)
    print(f"示例知识图谱已保存至 {OUT_JSON}")
    print(f"节点数: {len(nodes)}, 关系数: {len(relations)}")
    print(f"PROTEIN 节点: {len(proteins)}, GoTerm 节点: {len(go_terms_dict)}")
    print(f"HAS_FUNCTION 关系: {len(protein_go_edges)}")
    return kg

if __name__ == "__main__":
    build_sample_kg()