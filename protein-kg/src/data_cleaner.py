"""
蛋白质数据清洗器 — 按结构等级保留功能
"""
import re
import hashlib
from typing import Dict, List, Optional
from datetime import datetime

class ProteinDataCleaner:
    
    VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")
    
    # 结构证据等级
    STRUCTURE_TIER = {
        "experimental": 1,   # PDB 实验结构
        "predicted": 2,      # AlphaFold 预测
        "homology": 3,       # 同源建模
        "sequence_only": 4   # 只有序列
    }
    
    def __init__(self):
        self.stats = {"total": 0, "passed": 0, "removed": {}}
    
    def clean_batch(self, proteins: List[Dict], source: str) -> List[Dict]:
        self.stats["total"] = len(proteins)
        
        # 第一轮：序列合法性
        valid = []
        for p in proteins:
            if self._valid_sequence(p.get("sequence", "")):
                valid.append(p)
            else:
                self._log("invalid_sequence")
        
        # 第二轮：功能完整性
        with_function = []
        for p in valid:
            if self._has_function(p):
                with_function.append(p)
            else:
                self._log("no_function")
        
        # 第三轮：标记结构等级
        for p in with_function:
            p["structure_tier"] = self._assign_structure_tier(p)
            p["hash"] = hashlib.md5(p.get("sequence","").encode()).hexdigest()[:12]
        
        # 第四轮：去冗余（同序列保留结构等级最高的）
        best = {}
        for p in with_function:
            h = p["hash"]
            if h not in best or p["structure_tier"] < best[h]["structure_tier"]:
                best[h] = p
        
        cleaned = list(best.values())
        self.stats["passed"] = len(cleaned)
        
        print(f"\n🧹 清洗: {self.stats['total']}→{len(cleaned)}")
        print(f"   移除: {dict(self.stats['removed'])}")
        
        # 统计结构等级分布
        tiers = {}
        for p in cleaned:
            t = p.get("structure_tier", 4)
            tiers[t] = tiers.get(t, 0) + 1
        tier_names = {1: "实验结构", 2: "预测结构", 3: "同源建模", 4: "仅序列"}
        print(f"   结构等级: {', '.join(f'{tier_names[k]}:{v}' for k,v in sorted(tiers.items()))}")
        
        return cleaned
    
    def _valid_sequence(self, seq: str) -> bool:
        if not seq or len(seq) < 20 or len(seq) > 50000:
            return False
        return set(seq.upper()).issubset(self.VALID_AA)
    
    def _has_function(self, protein: Dict) -> bool:
        """有 GO 注释或有已知结构域的才保留"""
        name = protein.get("name", "")
        desc = protein.get("description", "")
        # 排除纯假设蛋白、未知功能蛋白
        unknown_keywords = ["uncharacterized", "hypothetical", "unknown", "putative", "predicted"]
        for kw in unknown_keywords:
            if kw.lower() in name.lower() or kw.lower() in desc.lower():
                return False
        return True
    
    def _assign_structure_tier(self, protein: Dict) -> int:
        """分配结构证据等级"""
        name = (protein.get("name", "") + " " + protein.get("description", "")).lower()
        
        if any(kw in name for kw in ["pdb", "crystal", "nmr", "x-ray"]):
            return 1  # 实验结构
        if any(kw in name for kw in ["alphafold", "structure prediction"]):
            return 2  # 预测结构
        if any(kw in name for kw in ["homolog", "domain", "family"]):
            return 3  # 同源建模
        return 4  # 只有序列
    
    def _log(self, reason: str):
        self.stats["removed"][reason] = self.stats["removed"].get(reason, 0) + 1


if __name__ == "__main__":
    from local_loader import LocalProteinLoader
    
    print("测试清洗器...")
    loader = LocalProteinLoader("data/human_proteome.fasta")
    raw = loader.parse_fasta()
    print(f"原始: {len(raw)} 条")
    
    cleaner = ProteinDataCleaner()
    cleaned = cleaner.clean_batch(raw, "UniProt")
    
    # 展示结构等级分布
    for p in cleaned[:5]:
        print(f"  {p['uniprot_id']}: tier={p.get('structure_tier','?')} | {p['name'][:50]} | {p['length']}aa")