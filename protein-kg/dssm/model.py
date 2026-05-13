import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel

class DualEncoder(nn.Module):
    """双塔模型：Query塔(文本) + Doc塔(蛋白序列)，带投影层对齐维度"""
    def __init__(self, query_model_name, doc_model_name, projection_dim=256):
        super().__init__()
        # Query塔：BioBERT
        self.query_tokenizer = AutoTokenizer.from_pretrained(query_model_name)
        self.query_encoder = AutoModel.from_pretrained(query_model_name)
        self.query_proj = nn.Linear(self.query_encoder.config.hidden_size, projection_dim)

        # Doc塔：ESM-2
        self.doc_tokenizer = AutoTokenizer.from_pretrained(doc_model_name)
        self.doc_encoder = AutoModel.from_pretrained(doc_model_name)
        self.doc_proj = nn.Linear(self.doc_encoder.config.hidden_size, projection_dim)

        self.projection_dim = projection_dim

    def encode_query(self, texts):
        device = next(self.parameters()).device
        inputs = self.query_tokenizer(texts, return_tensors="pt", padding=True,
                                       truncation=True, max_length=128).to(device)
        with torch.no_grad():
            outputs = self.query_encoder(**inputs)
        attention_mask = inputs["attention_mask"]
        embeddings = self._mean_pooling(outputs.last_hidden_state, attention_mask)
        # 投影到公共维度
        projected = self.query_proj(embeddings)
        return projected

    def encode_doc(self, sequences):
        device = next(self.parameters()).device
        inputs = self.doc_tokenizer(sequences, return_tensors="pt", padding=True,
                                    truncation=True, max_length=512).to(device)
        with torch.no_grad():
            outputs = self.doc_encoder(**inputs)
        attention_mask = inputs["attention_mask"]
        embeddings = self._mean_pooling(outputs.last_hidden_state, attention_mask)
        # 投影到公共维度
        projected = self.doc_proj(embeddings)
        return projected

    @staticmethod
    def _mean_pooling(token_embeddings, attention_mask):
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)