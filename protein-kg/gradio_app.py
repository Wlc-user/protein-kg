# gradio_app.py
# 放置路径：protein-kg/gradio_app.py
# 启动命令：python gradio_app.py
"""
蛋白质知识图谱交互式可视化界面
依赖：pip install gradio requests matplotlib
"""

import gradio as gr
import requests
import time
import matplotlib.pyplot as plt
import io

API_BASE = "http://localhost:8001"   # 改成你 API 实际端口

def search_similar(sequence, top_k):
    if not sequence.strip():
        return None, "请输入蛋白质序列"
    t0 = time.time()
    try:
        resp = requests.post(
            f"{API_BASE}/search",
            json={"sequence": sequence, "top_k": int(top_k)},
            timeout=30
        )
        resp.raise_for_status()
        results = resp.json()
    except Exception as e:
        return None, f"API 请求失败: {str(e)}"
    elapsed = (time.time() - t0) * 1000
    if not results:
        return None, "未找到相似蛋白质"
    table_data = []
    for r in results:
        table_data.append([
            r.get("protein_id", "N/A"),
            r.get("name", "N/A")[:60],
            f"{r.get('similarity', 0):.4f}",
            r.get("length", 0)
        ])
    fig, ax = plt.subplots(figsize=(8, 3))
    scores = [r.get("similarity", 0) for r in results]
    ids = [r.get("protein_id", "") for r in results]
    colors = ['#2ecc71' if s > 0.8 else '#3498db' if s > 0.6 else '#e74c3c' for s in scores]
    ax.barh(range(len(scores)), scores, color=colors)
    ax.set_yticks(range(len(scores)))
    ax.set_yticklabels(ids)
    ax.set_xlabel("相似度 (内积)")
    ax.set_title(f"Top-{top_k} 相似蛋白质 (查询耗时 {elapsed:.1f}ms)")
    ax.invert_yaxis()
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close()
    headers = ["蛋白ID", "名称", "相似度", "序列长度"]
    return table_data, buf

def get_protein_info(protein_id):
    if not protein_id.strip():
        return ""
    try:
        resp = requests.get(f"{API_BASE}/protein/{protein_id}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"查询失败: {str(e)}"
    info_text = f"""
### 蛋白质详情：{protein_id}
| 属性 | 值 |
|------|----|
| ID | {data.get('protein_id', 'N/A')} |
| 名称 | {data.get('name', 'N/A')} |
| 序列长度 | {data.get('length', 'N/A')} |
"""
    return info_text

def search_by_function(keyword):
    if not keyword.strip():
        return ""
    try:
        resp = requests.get(f"{API_BASE}/graph/function/{keyword}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return f"查询失败: {str(e)}"
    proteins = data.get("proteins", [])
    if not proteins:
        return f"未找到与「{keyword}」相关的蛋白质"
    lines = [f"### 关键字「{keyword}」匹配 {len(proteins)} 个结果"]
    for p in proteins[:20]:
        lines.append(f"- `{p.get('id', 'N/A')}`: {p.get('name', '')[:50]}")
    if len(proteins) > 20:
        lines.append(f"... 还有 {len(proteins) - 20} 条结果")
    return "\n".join(lines)

def health_check():
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        data = resp.json()
        return f"✅ 服务正常 | 已加载蛋白质: {data.get('total_proteins', '未知')}"
    except:
        return "❌ 服务不可用，请先启动 API"

with gr.Blocks(title="Protein-KG 可视化平台", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🧬 蛋白质知识图谱可视检索平台
    基于 ESM-2 嵌入 + Faiss 检索 + Neo4j 图数据库 | 19417 条人类蛋白质组
    """)
    with gr.Tab("🔍 序列相似检索"):
        with gr.Row():
            with gr.Column(scale=2):
                seq_input = gr.Textbox(
                    label="输入蛋白质序列",
                    placeholder="例如：MEEPQSDPSVEPPLSQETFSDLWKLL...",
                    lines=3
                )
                with gr.Row():
                    top_k = gr.Slider(minimum=1, maximum=20, value=5, step=1, label="返回结果数")
                    search_btn = gr.Button("搜索", variant="primary")
            with gr.Column(scale=1):
                status_text = gr.Markdown("等待输入...")
        result_table = gr.Dataframe(
            headers=["蛋白ID", "名称", "相似度", "序列长度"],
            label="检索结果",
            interactive=False
        )
        similarity_plot = gr.Image(label="相似度分布", type="filepath")
        search_btn.click(
            fn=search_similar,
            inputs=[seq_input, top_k],
            outputs=[result_table, similarity_plot]
        )
    with gr.Tab("📋 蛋白详情查询"):
        pid_input = gr.Textbox(label="输入蛋白质 ID（如 P04637）")
        info_btn = gr.Button("查询详情")
        info_output = gr.Markdown()
        info_btn.click(fn=get_protein_info, inputs=pid_input, outputs=info_output)
    with gr.Tab("🏷️ 功能检索"):
        func_input = gr.Textbox(label="输入功能关键字（如 kinase, receptor）")
        func_btn = gr.Button("搜索")
        func_output = gr.Markdown()
        func_btn.click(fn=search_by_function, inputs=func_input, outputs=func_output)
    with gr.Tab("💚 系统状态"):
        health_btn = gr.Button("检查服务状态")
        health_output = gr.Markdown()
        health_btn.click(fn=health_check, inputs=[], outputs=health_output)
    gr.Markdown("---\n📊 [GitHub](https://github.com/Wlc-user/protein-kg) | 技术栈: ESM-2 · Faiss · FastAPI · Neo4j · Gradio")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)