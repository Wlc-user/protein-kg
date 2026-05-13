"""ESMFold 蛋白质结构预测 — RTX 4050 6GB"""
import torch

# 加载模型（第一次会下载 ~3GB）
model = torch.hub.load('facebookresearch/esm:main', 'esmfold_v1')
model = model.cuda()  # 使用 GPU
model.eval()

# 预测序列
sequence = "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQ"
with torch.no_grad():
    result = model.infer_pdb(sequence)

# 保存为 PDB 文件
with open("../data/predicted_structure.pdb", "w") as f:
    f.write(result)
print("PDB 文件已保存: data/predicted_structure.pdb")

# 提取结构特征
from src.alphafold.structure import AlphaFoldStructure
af = AlphaFoldStructure()
contact_map = af.extract_contacts("../data/predicted_structure.pdb")
features = af.flatten_features(contact_map)
print(f"结构特征维度: {features.shape}")
print(f"前5维: {features[:5]}")