"""
蛋白质数据基础可视化（自动处理 gzip 压缩的 FASTA）
"""
import json
import gzip
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from Bio import SeqIO
import numpy as np
from collections import Counter

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# 1. 读取 FASTA（自动检测是否为 gzip 压缩）
print("读取 FASTA 序列...")
fasta_path = DATA_DIR / "human_proteome.fasta"

# 检查文件头
with open(fasta_path, 'rb') as f:
    magic = f.read(2)
is_gzipped = (magic == b'\x1f\x8b')

if is_gzipped:
    print("检测到 gzip 压缩，自动解压...")
    handle = gzip.open(fasta_path, 'rt', encoding='utf-8')
else:
    handle = open(fasta_path, 'r', encoding='utf-8')

seq_lengths = []
for record in SeqIO.parse(handle, "fasta"):
    seq_lengths.append(len(record.seq))
handle.close()

print(f"总共 {len(seq_lengths)} 条序列")

# 2. 读取 JSON（使用 relations 字段）
print("读取 JSON 节点和关系...")
json_path = DATA_DIR / "kg_full_export.json"
with open(json_path, "r", encoding="utf-8") as f:
    kg = json.load(f)

nodes = kg.get("nodes", [])
relations = kg.get("relations", [])      # 注意：你的 JSON 中是 "relations"

print(f"节点总数: {len(nodes)}")
print(f"关系总数: {len(relations)}")

# 节点类型统计
node_types = [node.get("type") for node in nodes if node.get("type")]
type_counts = Counter(node_types)
print("节点类型分布:", type_counts)

# 关系类型统计
rel_types = [rel.get("type") for rel in relations if rel.get("type")]
rel_counts = Counter(rel_types)
print("关系类型分布:", rel_counts)

# ---------- 绘图 ----------
sns.set_style("whitegrid")
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 子图1: 序列长度分布
sns.histplot(seq_lengths, bins=50, kde=True, ax=axes[0,0], color="steelblue")
axes[0,0].set_title("Protein Sequence Length Distribution")
axes[0,0].set_xlabel("Amino acid count")
axes[0,0].set_ylabel("Frequency")

# 子图2: 节点类型分布条形图
if type_counts:
    types = list(type_counts.keys())
    counts = list(type_counts.values())
    axes[0,1].bar(types, counts, color="coral")
    axes[0,1].set_title("Node Type Distribution")
    axes[0,1].set_xticklabels(types, rotation=45, ha="right")
    axes[0,1].set_ylabel("Count")
else:
    axes[0,1].text(0.5, 0.5, "No node types found", ha="center", va="center")

# 子图3: 关系类型分布条形图
if rel_counts:
    rel_types_list = list(rel_counts.keys())
    rel_counts_list = list(rel_counts.values())
    axes[1,0].bar(rel_types_list, rel_counts_list, color="lightgreen")
    axes[1,0].set_title("Relation Type Distribution")
    axes[1,0].set_xticklabels(rel_types_list, rotation=45, ha="right")
    axes[1,0].set_ylabel("Count")
else:
    axes[1,0].text(0.5, 0.5, "No relations found", ha="center", va="center")
    axes[1,0].set_title("Relation Types (none)")

# 子图4: 统计摘要文本
textstr = f"Total proteins (FASTA): {len(seq_lengths)}\nMean length: {np.mean(seq_lengths):.1f}\nMedian length: {np.median(seq_lengths):.1f}\nTotal nodes in JSON: {len(nodes)}\nNode types: {', '.join(type_counts.keys()) if type_counts else 'none'}\nRelation types: {', '.join(rel_counts.keys()) if rel_counts else 'none'}"
axes[1,1].axis("off")
axes[1,1].text(0.1, 0.5, textstr, fontsize=11, va="center", family="monospace")
axes[1,1].set_title("Summary Statistics")

plt.tight_layout()
plt.savefig(REPORT_DIR / "protein_basic_stats.png", dpi=150)
plt.close()
print(f"图表已保存至 {REPORT_DIR / 'protein_basic_stats.png'}")

# 输出文本摘要
with open(REPORT_DIR / "protein_stats_summary.txt", "w", encoding="utf-8") as f:
    f.write(f"Total proteins (from FASTA): {len(seq_lengths)}\n")
    f.write(f"Mean sequence length: {np.mean(seq_lengths):.1f}\n")
    f.write(f"Median sequence length: {np.median(seq_lengths):.1f}\n")
    f.write(f"Total nodes in JSON: {len(nodes)}\n")
    f.write(f"Node type distribution: {dict(type_counts)}\n")
    f.write(f"Relation type distribution: {dict(rel_counts)}\n")
print("文本摘要已保存至 reports/protein_stats_summary.txt")
