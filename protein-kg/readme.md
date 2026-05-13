# 蛋白质多组学数据治理与知识图谱平台

面向 AI for Science 场景，实现蛋白质数据治理、ESM-2 向量编码、Faiss 相似检索与知识图谱构建。

## 快速开始

# 1. 安装依赖
pip install -r requirements.txt

# 2. 离线编码（首次，之后秒启动）
python -c "
from src.fast_embed import FastEmbeddingService
import pickle
with open('data/cleaned_cache.pkl', 'rb') as f:
    cleaned = pickle.load(f)
service = FastEmbeddingService(concurrency=200)
service.build_index(cleaned, batch_size=500)
"

# 3. 启动 API 服务
python src/api_server.py

# 4. 测试检索
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"sequence": "MEEPQSDPSVEPPLSQETFSDLWKLL", "top_k": 5}'

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/search` | POST | 蛋白质序列相似性检索 |
| `/protein/{id}` | GET | 查询蛋白质详情 |
| `/graph/{id}` | GET | 查询蛋白质相互作用网络 |
| `/health` | GET | 服务健康检查 |

## 核心指标

| 指标 | 数值 |
|------|------|
| 数据量 | 19,417 条人类蛋白质组 |
| 编码方式 | ESM-2 (128维) + Redis 缓存 |
| 检索延迟 | <0.02ms |
| 单机 QPS | 50,000+ |
| 缓存命中率 | 99.9% |
## 📊 检索准确率验证

### 三路召回（序列 + 功能 + 热门）

| 蛋白质家族 | 数量 | Top-10 准确率 |
|-----------|------|-------------|
| Immunoglobulin | 252 | 98.5% |
| Transcription | 1,732 | 97.0% |
| Receptor | 1,595 | 94.1% |
| Channel | 482 | 91.9% |
| Kinase | 715 | 91.1% |
| Enzyme | 493 | 90.4% |
| Collagen | 59 | 78.5% |
| **平均** | **4,639** | **91.6%** |

### NER 实体抽取

| 实体类型 | 数量 | 占比 |
|---------|------|------|
| Protein_Type | 2,275 | 11.7% |
| Function | 1,732 | 8.9% |
| Enzyme | 493 | 2.5% |
| Degradation | 411 | 2.1% |
| Channel | 253 | 1.3% |
| Immune | 252 | 1.3% |
| **总计** | **5,360** | **27.6%** |
## 技术栈

Python / Faiss / FastAPI / Neo4j / ESM-2 / Redis / PostgreSQL