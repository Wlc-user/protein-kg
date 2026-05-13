import os

CLEANED_CACHE = "data/cleaned_cache.pkl"
DSSM_TRAINING_CACHE = "data/dssm_training.pkl"

QUERY_MODEL_NAME = "dmis-lab/biobert-v1.1"
DOC_MODEL_NAME = "facebook/esm2_t6_8M_UR50D"

OUTPUT_DIR = "dssm"
QUERY_ENCODER_PATH = os.path.join(OUTPUT_DIR, "query_encoder")
DOC_ENCODER_PATH = os.path.join(OUTPUT_DIR, "doc_encoder")
FAISS_INDEX_PATH = os.path.join(OUTPUT_DIR, "faiss_dssm.index")
ID_MAP_PATH = os.path.join(OUTPUT_DIR, "id_map.pkl")

BATCH_SIZE = 8
EPOCHS = 3
LEARNING_RATE = 2e-5
DEVICE = "cuda" if __import__('torch').cuda.is_available() else "cpu"
MAX_TEXT_LENGTH = 128
MAX_SEQ_LENGTH = 512
