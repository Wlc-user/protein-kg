import pickle
import numpy as np
import faiss
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from .config import *
from .dataset import ProteinTextSeqDataset
from .model import DualEncoder
import os

def build_index():
    dataset = ProteinTextSeqDataset(max_seq_len=MAX_SEQ_LENGTH)
    model = DualEncoder(QUERY_ENCODER_PATH, DOC_ENCODER_PATH, projection_dim=256).to(DEVICE)
    model.eval()

    loader = DataLoader(dataset, batch_size=32, shuffle=False)
    ids = []
    all_embeddings = []
    for _, seqs, batch_ids in tqdm(loader, desc="Building index"):
        with torch.no_grad():
            emb = model.encode_doc(list(seqs))
        all_embeddings.append(emb.cpu().numpy())
        ids.extend(batch_ids)

    embeddings = np.concatenate(all_embeddings, axis=0).astype('float32')
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(ID_MAP_PATH, "wb") as f:
        pickle.dump(ids, f)
    print(f"✅ 索引构建完成：{len(ids)} 条蛋白质，向量维度 {dim}")

if __name__ == "__main__":
    build_index()
