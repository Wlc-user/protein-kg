"""
命名实体识别 - 使用BioBERT预训练模型
"""
from transformers import pipeline
from typing import List, Dict, Tuple
import re
import warnings
warnings.filterwarnings("ignore")


class ProteinNER:
    """使用BioBERT进行蛋白质/基因/疾病实体识别"""
    
    def __init__(self, model_name: str = "dmis-lab/biobert-base-cased-v1.1"):
        print(f"正在加载BioBERT模型: {model_name}...")
        print("首次下载约1.5GB，请稍候...")
        self.nlp = pipeline(
            "ner", 
            model=model_name, 
            tokenizer=model_name,
            aggregation_strategy="simple"
        )
        print("✅ BioBERT模型加载完成")
    
    def extract(self, text: str) -> List[Dict]:
        """从文本中提取实体"""
        text = text.strip().replace('\n', ' ')
        entities = self.nlp(text)
        return [{
            "entity": e["word"],
            "type": e["entity_group"],
            "score": round(e["score"], 3),
            "start": e.get("start", 0),
            "end": e.get("end", 0)
        } for e in entities]
    
    def extract_with_positions(self, text: str) -> List[Tuple[str, str, int, int]]:
        """提取实体并返回位置信息"""
        entities = self.extract(text)
        return [(e["entity"], e["type"], e["start"], e["end"]) for e in entities]
    
    def extract_relations(self, text: str, window_size: int = 100) -> List[Tuple[str, str, str]]:
        """基于实体位置提取关系"""
        entities = self.extract_with_positions(text)
        relations = []
        entities_sorted = sorted(entities, key=lambda x: x[2])
        
        for i in range(len(entities_sorted)):
            for j in range(i + 1, len(entities_sorted)):
                e1, e2 = entities_sorted[i], entities_sorted[j]
                if abs(e1[2] - e2[2]) < window_size:
                    between = text[e1[2]:e2[3]].lower()
                    if any(w in between for w in ['interact', 'bind', 'associate']):
                        rel_type = 'interacts_with'
                    elif any(w in between for w in ['inhibit', 'suppress', 'block']):
                        rel_type = 'inhibits'
                    elif any(w in between for w in ['activate', 'promote', 'induce']):
                        rel_type = 'activates'
                    else:
                        rel_type = 'co-occurs'
                    relations.append((e1[0], rel_type, e2[0]))
        return relations


class SimpleProteinNER:
    """轻量级规则NER（备用）"""
    
    PROTEINS = {'BRCA1', 'BRCA2', 'TP53', 'EGFR', 'KRAS', 'HER2', 'MYC', 'AKT1', 'PTEN', 'RB1', 'APC', 'VEGF', 'CDK4', 'CDK6', 'PD-1', 'PD-L1', 'CTLA-4', 'RAS', 'RAF', 'MEK', 'ERK', 'PI3K', 'mTOR', 'NF-κB', 'TNF-α', 'IL-6', 'p53', 'Bcl-2', 'Bax', 'Caspase-3'}
    DISEASES = {'breast cancer', 'lung cancer', 'pancreatic cancer', 'prostate cancer', 'colorectal cancer', 'leukemia', 'lymphoma', 'melanoma', 'glioblastoma', 'alzheimer', 'parkinson', 'diabetes', 'obesity', 'fibrosis', 'cirrhosis'}
    
    def extract(self, text: str) -> List[Dict]:
        results = []
        for protein in self.PROTEINS:
            for match in re.finditer(r'\b' + re.escape(protein) + r'\b', text, re.IGNORECASE):
                results.append({"entity": match.group(), "type": "PROTEIN", "score": 0.85, "start": match.start(), "end": match.end()})
        for disease in self.DISEASES:
            for match in re.finditer(r'\b' + re.escape(disease) + r'\b', text, re.IGNORECASE):
                results.append({"entity": match.group(), "type": "DISEASE", "score": 0.80, "start": match.start(), "end": match.end()})
        # 去重
        seen, unique = set(), []
        for r in results:
            key = (r['entity'], r['type'])
            if key not in seen:
                seen.add(key)
                unique.append(r)
        return unique
    
    def extract_with_positions(self, text: str) -> List[Tuple[str, str, int, int]]:
        return [(e["entity"], e["type"], e["start"], e["end"]) for e in self.extract(text)]
    
    def extract_relations(self, text: str, window_size: int = 100) -> List[Tuple[str, str, str]]:
        entities = self.extract_with_positions(text)
        relations = []
        for i in range(len(entities)):
            for j in range(i+1, len(entities)):
                e1, e2 = entities[i], entities[j]
                if abs(e1[2] - e2[2]) < window_size:
                    relations.append((e1[0], "co-occurs", e2[0]))
        return relations


def get_ner(mode: str = "simple"):
    """工厂方法：获取NER实例"""
    if mode == "biobert":
        try:
            return ProteinNER()
        except Exception as e:
            print(f"⚠️ BioBERT加载失败: {e}，切换到轻量级模式")
            return SimpleProteinNER()
    else:
        return SimpleProteinNER()


if __name__ == '__main__':
    ner = get_ner("simple")
    result = ner.extract("BRCA1 interacts with TP53 in breast cancer")
    print("提取结果:", result)
