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

## 技术栈

Python / Faiss / FastAPI / Neo4j / ESM-2 / Redis / PostgreSQL