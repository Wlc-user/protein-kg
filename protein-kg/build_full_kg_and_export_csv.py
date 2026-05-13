"""
构建完整知识图谱（蛋白质+GO）并导出 CSV，不依赖 Neo4j
从 uniprot_sprot_human.dat.gz 解析蛋白质及其 GO 注释
"""

import gzip
import csv
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
UNIPROT_DAT = DATA_DIR / "uniprot_sprot_human.dat.gz"
PROTEIN_CSV = DATA_DIR / "proteins.csv"
PROTEIN_GO_CSV = DATA_DIR / "protein_go.csv"
GO_CSV = DATA_DIR / "go_terms.csv"

def parse_uniprot_dat():
    """解析 .dat.gz 文件，返回蛋白质信息、GO 关联、GO 信息"""
    proteins = {}          # uniprot_id -> {'gene_name': ..., 'organism': ...}
    protein_go = []        # (uniprot_id, go_id, evidence)
    go_terms = {}          # go_id -> {'name': ..., 'category': ...}
    
    print("开始解析 uniprot_sprot_human.dat.gz ...")
    with gzip.open(UNIPROT_DAT, 'rt', encoding='utf-8') as f:
        current_id = None
        current_gene = None
        current_org = None
        for line in f:
            line = line.rstrip('\n')
            if line.startswith('ID   '):
                # 新条目开始，提取ID (但 UniProt ID 通常在其他行)
                pass
            elif line.startswith('AC   '):
                # 获取 UniProt accession (一个蛋白质可能有多个)
                # 取第一个
                parts = line[5:].split(';')
                if parts:
                    current_id = parts[0].strip()
            elif line.startswith('DE   '):
                # 描述，这里我们省略，可以用后来补充
                pass
            elif line.startswith('GN   '):
                # 基因名称
                # 格式: GN   Name=BRCA1; Synonyms=...
                if 'Name=' in line:
                    gene_part = line[5:].split(';')[0]
                    if 'Name=' in gene_part:
                        current_gene = gene_part.split('=')[1].strip()
            elif line.startswith('OS   '):
                # 物种名称
                current_org = line[5:].strip()
            elif line.startswith('DR   GO;'):
                # 解析 GO 行： DR   GO; GO:0005737; C:cytoplasm; ...
                parts = line[6:].split(';')
                if len(parts) >= 2:
                    go_id = parts[1].strip()
                    go_name = parts[2].strip() if len(parts) >= 3 else ''
                    # 获取 category: 第二个字符 (C, F, P)
                    # GO:0005737 中 C 表示 Cellular component
                    category_code = go_id.split(':')[1][0] if ':' in go_id else ''
                    category_map = {'C': 'CC', 'F': 'MF', 'P': 'BP'}
                    category = category_map.get(category_code, 'unknown')
                    # 保存 GO term
                    if go_id not in go_terms:
                        go_terms[go_id] = {'name': go_name, 'category': category}
                    # 保存关联
                    if current_id:
                        protein_go.append((current_id, go_id))
            elif line.startswith('DR   PPI;'):
                # 可选：解析蛋白质相互作用 (取决于格式)
                # 这里暂不实现，因为可能没有，或者后期用 STRINGdb
                pass
            elif line.startswith('//'):
                # 条目结束，将当前蛋白质信息保存
                if current_id:
                    proteins[current_id] = {
                        'gene_name': current_gene or '',
                        'organism': current_org or 'Homo sapiens'
                    }
                current_id = None
                current_gene = None
                current_org = None

    print(f"解析完成：{len(proteins)} 个蛋白质，{len(go_terms)} 个 GO term，{len(protein_go)} 条关联")
    return proteins, protein_go, go_terms

def write_csvs(proteins, protein_go, go_terms):
    # 写入蛋白质表
    with open(PROTEIN_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['uniprot_id', 'gene_name', 'organism'])
        for uniprot, info in proteins.items():
            writer.writerow([uniprot, info['gene_name'], info['organism']])
    print(f"已写入 {PROTEIN_CSV}，{len(proteins)} 行")

    # 写入 GO 表
    with open(GO_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['go_id', 'name', 'category'])
        for go_id, info in go_terms.items():
            writer.writerow([go_id, info['name'], info['category']])
    print(f"已写入 {GO_CSV}，{len(go_terms)} 行")

    # 写入蛋白质-GO 关联
    with open(PROTEIN_GO_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['uniprot_id', 'go_id'])
        for uniprot, go_id in protein_go:
            writer.writerow([uniprot, go_id])
    print(f"已写入 {PROTEIN_GO_CSV}，{len(protein_go)} 行")

if __name__ == "__main__":
    proteins, protein_go, go_terms = parse_uniprot_dat()
    write_csvs(proteins, protein_go, go_terms)
    print("CSV 导出完成。R 语言可以直接读取这些文件进行分析。")