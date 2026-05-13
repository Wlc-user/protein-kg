# 创建 visualize_kg.py
import streamlit as st
import json
import networkx as nx
import plotly.graph_objects as go

st.title("🔬 蛋白质知识图谱可视化")

# 加载数据
with open("data/kg_full_export.json", "r", encoding='utf-8') as f:
    kg_data = json.load(f)

st.write(f"**总节点数:** {kg_data['metadata']['total_nodes']}")
st.write(f"**总关系数:** {kg_data['metadata']['total_relations']}")

# 搜索功能
entity = st.text_input("搜索实体 (如 BRCA1, TP53)")
if entity:
    relations = [r for r in kg_data['relations'] 
                 if r['source'] == entity or r['target'] == entity]
    st.write(f"找到 {len(relations)} 个关联:")
    for r in relations:
        st.write(f"  {r['source']} → {r['target']} ({r['type']})")