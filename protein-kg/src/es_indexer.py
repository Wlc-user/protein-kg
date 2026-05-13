from elasticsearch import AsyncElasticsearch
from .models import Protein

INDEX_NAME = "proteins"

INDEX_MAPPING = {
    "mappings": {
        "properties": {
            "uniprot_id": {"type": "keyword"},
            "entry_name": {"type": "keyword"},
            "protein_name": {"type": "text", "analyzer": "english"},
            "gene_name": {"type": "keyword"},
            "organism": {"type": "keyword"},
            "function_description": {"type": "text", "analyzer": "english"},
            "go_terms": {"type": "text"},
            "sequence": {"type": "text"}  # 可做模糊搜索
        }
    }
}

class ESIndexer:
    def __init__(self, url):
        self.client = AsyncElasticsearch(url)

    async def create_index(self):
        if not await self.client.indices.exists(index=INDEX_NAME):
            await self.client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
            print(f"📄 ES 索引 '{INDEX_NAME}' 创建成功")

    async def index_proteins(self, proteins: list[Protein]):
        """批量写入蛋白质文档"""
        actions = []
        for p in proteins:
            actions.append({"index": {"_index": INDEX_NAME, "_id": p.uniprot_id}})
            actions.append({
                "uniprot_id": p.uniprot_id,
                "entry_name": p.entry_name,
                "protein_name": p.protein_name,
                "gene_name": p.gene_name,
                "organism": p.organism,
                "function_description": p.function_description,
                "go_terms": " ".join([go["term"] for go in p.go_terms]),
                "sequence": p.sequence
            })
        if actions:
            resp = await self.client.bulk(body=actions, refresh=True)
            if resp.get("errors"):
                print("⚠️ ES 批量写入有错误:", resp)
            else:
                print(f"✅ ES 索引导入: {len(proteins)} 条")

    async def search_keyword(self, query: str, size: int = 10):
        """关键词搜索（倒排索引）"""
        result = await self.client.search(index=INDEX_NAME, body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["protein_name^3", "function_description^2", "go_terms"]
                }
            },
            "size": size
        })
        return [hit["_source"] for hit in result["hits"]["hits"]]

    async def close(self):
        await self.client.close()