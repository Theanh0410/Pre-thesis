import os
import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")
DOCUMENT_DIR = "/Users/macbook/Documents/LLM /server/documents"

chunks = []

# 1. Đọc và chia nhỏ văn bản
for filename in os.listdir(DOCUMENT_DIR):
    if filename.endswith(".txt") or filename.endswith(".md"):
        path = os.path.join(DOCUMENT_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Chunk theo độ dài
        words = content.split()
        chunk_size = 150
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            if len(chunk.strip()) > 20:
                chunks.append(chunk)

# 2. Chuyển thành embedding vector
embeddings = model.encode(chunks, convert_to_numpy=True)

# 3. Build FAISS index
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# 4. Lưu index và chunks
faiss.write_index(index, "rag_index.faiss")
with open("documents.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"✅ Đã build index xong với {len(chunks)} đoạn văn bản.")
