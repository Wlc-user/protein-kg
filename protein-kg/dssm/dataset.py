import pickle
import os
import torch
from torch.utils.data import Dataset
from .config import CLEANED_CACHE, DSSM_TRAINING_CACHE, MAX_SEQ_LENGTH
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
class ProteinTextSeqDataset(Dataset):
    def __init__(self, max_seq_len=512):
        self.max_seq_len = max_seq_len
        if os.path.exists(DSSM_TRAINING_CACHE):
            try:
                with open(DSSM_TRAINING_CACHE, "rb") as f:
                    self.pairs = pickle.load(f)
                if not self.pairs:
                    raise ValueError("Empty cache")
                print(f"从缓存加载训练数据: {DSSM_TRAINING_CACHE}，共 {len(self.pairs)} 条")
            except (EOFError, ValueError, pickle.UnpicklingError):
                print(f"缓存文件损坏或为空，删除后重新生成: {DSSM_TRAINING_CACHE}")
                os.remove(DSSM_TRAINING_CACHE)
                self._generate_cache()
        else:
            self._generate_cache()

    def _generate_cache(self):
        print(f"从 {CLEANED_CACHE} 生成训练数据...")
        with open(CLEANED_CACHE, "rb") as f:
            proteins = pickle.load(f)
        self.pairs = []
        for p in proteins:
            text = self._build_text(p)
            seq = p.get("sequence", "")[:self.max_seq_len]
            if len(seq) > 10 and text.strip():
                self.pairs.append({
                    "id": p.get("id", ""),
                    "text": text,
                    "sequence": seq
                })
        print(f"生成 {len(self.pairs)} 条训练样本")
        os.makedirs(os.path.dirname(DSSM_TRAINING_CACHE), exist_ok=True)
        with open(DSSM_TRAINING_CACHE, "wb") as f:
            pickle.dump(self.pairs, f)
        print(f"已缓存到 {DSSM_TRAINING_CACHE}")

    def _build_text(self, protein):
        parts = []
        pid = protein.get("id", "")
        name = protein.get("name", "")
        if name:
            parts.append(f"Protein {name}")
        if pid:
            parts.append(f"UniProt ID {pid}")
        tier = protein.get("structure_tier", "")
        if tier:
            parts.append(f"Structure tier: {tier}")
        return ". ".join(parts) if parts else ""

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        item = self.pairs[idx]
        return item["text"], item["sequence"], item["id"]