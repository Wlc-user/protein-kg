import json
import requests
import time
from tqdm import tqdm

# UniProt 单个蛋白质查询的 URL 模板，返回 JSON 格式
UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/{}?format=json"
# 从你之前提取的 ID 文件读取，请根据需要修改文件名
ID_FILE = "data/all_ids.json"
# 输出文件名
OUTPUT_FILE = "data/all_proteins.json"

# 读取 IDs
with open(ID_FILE, "r") as f:
    all_ids = json.load(f)

# 存储结果
results = []
for protein_id in tqdm(all_ids, desc="Fetching protein data"):
    try:
        # 根据模板生成实际的查询 URL
        resp = requests.get(UNIPROT_URL.format(protein_id), headers={"Accept": "application/json"})
        resp.raise_for_status()  # 若状态码不是 200，则抛出异常
        
        data = resp.json()
        # 提取 FUNCTION 注释
        function_text = "Function not annotated."
        if "comments" in data:
            for comment in data["comments"]:
                if comment["commentType"] == "FUNCTION":
                    function_text = " ".join([t.get("value", "") for t in comment.get("texts", [])]).strip()
                    break
        
        results.append({
            "id": protein_id,
            "name": protein_id,
            "function": function_text
        })
        
        # 遵守 API 使用规范，避免请求过快
        time.sleep(0.1)
        
    except Exception as e:
        print(f"\n⚠️ 获取 {protein_id} 失败: {e}")
        results.append({
            "id": protein_id,
            "name": protein_id,
            "function": "Error fetching data"
        })
        time.sleep(1)

# 保存结果
with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
    
print(f"\n✅ 成功获取 {len(results)} 个蛋白质的数据，已保存到 {OUTPUT_FILE}")