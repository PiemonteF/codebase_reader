import os
from dotenv import load_dotenv
from lancedb.embeddings import EmbeddingFunctionRegistry

load_dotenv()

# Embedding configuration
if os.getenv("OPENAI_API_KEY"):
    print("Using OpenAI")
    MODEL_NAME = "text-embedding-3-large"
    registry = EmbeddingFunctionRegistry.get_instance()
    model = registry.get("openai").create(name=MODEL_NAME, max_retries=2)
    EMBEDDING_DIM = model.ndims()
    MAX_TOKENS = 8000
