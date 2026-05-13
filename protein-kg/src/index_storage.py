import faiss, pickle, os, numpy as np

INDEX_DIR = "data/index"

def save_index(service, index_name="fast_embed"):
    os.makedirs(INDEX_DIR, exist_ok=True)
    index_path = os.path.join(INDEX_DIR, f"{index_name}.faiss")
    ids_path = os.path.join(INDEX_DIR, f"{index_name}_ids.pkl")
    
    faiss.write_index(service.index, index_path)
    with open(ids_path, 'wb') as f:
        pickle.dump(service.protein_ids, f)
    print(f"索引已保存: {index_path} ({len(service.protein_ids)} 个向量)")

def load_index(service, index_name="fast_embed"):
    index_path = os.path.join(INDEX_DIR, f"{index_name}.faiss")
    ids_path = os.path.join(INDEX_DIR, f"{index_name}_ids.pkl")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"索引文件不存在: {index_path}")
    
    service.index = faiss.read_index(index_path)
    with open(ids_path, 'rb') as f:
        service.protein_ids = pickle.load(f)
    print(f"索引加载完成: {len(service.protein_ids)} 个向量")
