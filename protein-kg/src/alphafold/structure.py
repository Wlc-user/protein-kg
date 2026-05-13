"""AlphaFold 结构特征提取（从 PDB 文件提取残基距离矩阵）"""
import numpy as np
from scipy.spatial.distance import cdist

class AlphaFoldStructure:
    def __init__(self):
        print("AlphaFold structure extractor ready")
    
    def extract_contacts(self, pdb_path):
        """从 PDB 文件提取 Cα 原子坐标，计算接触图"""
        ca_coords = []
        with open(pdb_path) as f:
            for line in f:
                if line.startswith("ATOM") and line[12:16].strip() == "CA":
                    x = float(line[30:38])
                    y = float(line[38:46])
                    z = float(line[46:54])
                    ca_coords.append([x, y, z])
        
        if len(ca_coords) < 10:
            return np.zeros((10, 10))
        
        coords = np.array(ca_coords)
        dist_matrix = cdist(coords, coords)
        contact_map = (dist_matrix < 8.0).astype(np.float32)
        return contact_map
    
    def flatten_features(self, contact_map):
        """接触图展平为固定维度特征向量"""
        upper_tri = contact_map[np.triu_indices_from(contact_map, k=1)]
        hist, _ = np.histogram(upper_tri, bins=10, range=(0, 1))
        return hist.astype(np.float32) / len(upper_tri)