import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from .config import *
from .dataset import ProteinTextSeqDataset
from .model import DualEncoder
import os

def train():
    dataset = ProteinTextSeqDataset(max_seq_len=MAX_SEQ_LENGTH)
    data_loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    model = DualEncoder(QUERY_MODEL_NAME, DOC_MODEL_NAME, projection_dim=256).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    loss_fn = torch.nn.CrossEntropyLoss()
    temperature = 0.07

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0
        for batch in tqdm(data_loader, desc=f"Epoch {epoch+1}/{EPOCHS}"):
            texts, seqs, _ = batch
            q_emb = model.encode_query(texts)
            d_emb = model.encode_doc(seqs)

            logits = torch.matmul(q_emb, d_emb.T) / temperature
            labels = torch.arange(len(logits)).to(DEVICE)

            loss = loss_fn(logits, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch {epoch+1} average loss: {total_loss / len(data_loader):.4f}")

    # 保存模型
    os.makedirs(QUERY_ENCODER_PATH, exist_ok=True)
    os.makedirs(DOC_ENCODER_PATH, exist_ok=True)
    model.query_tokenizer.save_pretrained(QUERY_ENCODER_PATH)
    model.query_encoder.save_pretrained(QUERY_ENCODER_PATH)
    model.doc_tokenizer.save_pretrained(DOC_ENCODER_PATH)
    model.doc_encoder.save_pretrained(DOC_ENCODER_PATH)
    print(f"模型已保存至 {QUERY_ENCODER_PATH} 和 {DOC_ENCODER_PATH}")

if __name__ == "__main__":
    train()