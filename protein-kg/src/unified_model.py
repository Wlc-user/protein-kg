"""
统一蛋白质数据模型：融合序列+结构+功能+相互作用
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import hashlib

@dataclass
class UnifiedProtein:
    """统一的蛋白质数据模型"""
    
    # 一级结构
    uniprot_id: str
    name: str
    gene: str = ""
    organism: str = ""
    sequence: str = ""
    length: int = 0
    
    # 二级结构
    secondary_structure: str = ""  # DSSP格式
    helix_ratio: float = 0.0
    sheet_ratio: float = 0.0
    coil_ratio: float = 0.0
    
    # 三级结构
    pdb_id: str = ""
    has_experimental_structure: bool = False
    has_predicted_structure: bool = False
    contact_map: Optional[bytes] = None  # 序列化的接触图
    
    # 四级结构
    interactions: List[Dict] = field(default_factory=list)  # STRING相互作用
    
    # 功能注释
    functions: List[str] = field(default_factory=list)
    go_terms: List[str] = field(default_factory=list)
    kegg_pathways: List[str] = field(default_factory=list)
    
    # 手性校验
    chirality_valid: bool = True
    chirality_issues: List[str] = field(default_factory=list)
    
    # 元数据
    source: str = ""  # UniProt/PDB/AlphaFold
    source_id: str = ""
    imported_at: str = ""
    hash: str = ""
    
    def compute_hash(self):
        """基于序列的MD5哈希"""
        self.hash = hashlib.md5(self.sequence.encode()).hexdigest()[:12]
    
    def to_pg_row(self) -> Dict:
        """转为 PostgreSQL 一行"""
        return {
            "uniprot_id": self.uniprot_id,
            "name": self.name,
            "gene": self.gene,
            "organism": self.organism,
            "sequence": self.sequence,
            "length": self.length,
            "helix_ratio": self.helix_ratio,
            "sheet_ratio": self.sheet_ratio,
            "coil_ratio": self.coil_ratio,
            "pdb_id": self.pdb_id,
            "has_experimental_structure": self.has_experimental_structure,
            "has_predicted_structure": self.has_predicted_structure,
            "functions": "|".join(self.functions),
            "go_terms": "|".join(self.go_terms),
            "source": self.source,
            "source_id": self.source_id,
            "hash": self.hash,
            "chirality_valid": self.chirality_valid
        }
    
    def to_embedding_input(self) -> str:
        """转为推荐系统的输入特征"""
        # 序列 + 功能文本拼在一起
        func_text = " ".join(self.functions + self.go_terms)
        return f"{self.sequence[:500]} [SEP] {func_text[:200]}"