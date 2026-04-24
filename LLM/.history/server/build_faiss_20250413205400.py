import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load documents
with open("documents.json", "r", encoding="utf-8") as f:
    documents = json.load(f)

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Encode documents
embeddings = model.encode(documents)
embeddings = np.array(embeddings).astype("float32")

# Build FAISS index
index = faiss.IndexFlatL2(embeddings.shape[1])
index.add(embeddings)

# Save index
faiss.write_index(index, "rag_index.faiss")

print("✅ FAISS index saved as 'rag_index.faiss'")
