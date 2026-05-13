"""ProtBERT 蛋白质序列编码"""
import torch
import numpy as np
from transformers import BertModel, BertTokenizer

class ProtBERTEncoder:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.tokenizer = BertTokenizer.from_pretrained("Rostlab/prot_bert")
        self.model = BertModel.from_pretrained("Rostlab/prot_bert").to(device)
        self.model.eval()
        print(f"ProtBERT loaded on {device}")
    
    def encode(self, sequence):
        seq = " ".join(list(sequence[:500]))
        inputs = self.tokenizer(seq, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
            emb = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
        return emb.astype(np.float32)