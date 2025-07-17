import os

# Directory containing data files to process
DATA_DIR = os.getenv("DATA_DIR", "data/")

# Model and server config
MODEL_PATH = os.getenv("LLM_MODEL_PATH", "Mixtral-8x7B-Instruct-v0.1.Q6_K.gguf")
SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", "8000"))
N_THREADS = int(os.getenv("LLM_THREADS", "8"))
N_CTX = int(os.getenv("LLM_CTX", "4096"))

# Chunking and batching defaults
PRE_TOKEN_COUNT = int(os.getenv("PRE_TOKEN_COUNT", "0"))
POST_TOKEN_COUNT = int(os.getenv("POST_TOKEN_COUNT", "0"))

# Adaptive controller defaults
MIN_RAM = float(os.getenv("MIN_RAM", "10.0"))
MAX_CPU = float(os.getenv("MAX_CPU", "80.0"))
BASE_CHUNK_SIZE = int(os.getenv("BASE_CHUNK_SIZE", "100"))
BASE_PROCESSES = int(os.getenv("BASE_PROCESSES", "4"))
BASE_BATCH_SIZE = int(os.getenv("BASE_BATCH_SIZE", "10"))
MAX_CHUNK_SIZE = int(os.getenv("MAX_CHUNK_SIZE", "512"))
MAX_PROCESSES = int(os.getenv("MAX_PROCESSES", "16"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "64"))