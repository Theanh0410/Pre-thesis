import os
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# --- CONFIG ---
DATA_DIR = "rag_health_data"
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "llama3"

# --- STEP 1: Chunk Markdown files ---
def chunk_documents(data_dir):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = []

    for source_dir in Path(data_dir).iterdir():
        if not source_dir.is_dir():
            continue
        for file in source_dir.glob("*.md"):
            with open(file, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            chunks = text_splitter.create_documents([raw_text])
            for chunk in chunks:
                chunk.metadata = {"source": str(file)}
                documents.append(chunk)

    return documents

# --- STEP 2: Embed documents into ChromaDB ---
def embed_documents(documents):
    embedding_function = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma.from_documents(documents, embedding_function, persist_directory=CHROMA_DB_DIR)
    vectordb.persist()
    return vectordb

# --- STEP 3: Flask API with Ollama + Retrieval ---
app = Flask(__name__)
CORS(app)

@app.route("/api/healthchat", methods=["POST"])
def health_chat():
    data = request.get_json()
    query = data.get("query")

    embedding_function = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding_function)

    docs = vectordb.similarity_search(query, k=4)
    context = "\n\n".join([doc.page_content for doc in docs])

    payload = {
        "model": MODEL_NAME,
        "prompt": f"You are a compassionate mental health advisor. Based on the following context, answer kindly:\n\n{context}\n\nQuestion: {query}\nAnswer:",
        "stream": False
    }

    import requests
    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return jsonify(response.json())

if __name__ == "__main__":
    print("⏳ Chunking documents...")
    docs = chunk_documents(DATA_DIR)
    print(f"✅ {len(docs)} chunks created.")

    print("🔗 Embedding to ChromaDB...")
    embed_documents(docs)
    print("✅ Embedding completed and saved to ChromaDB.")

    print("🚀 Starting Flask API on http://localhost:5000")
    app.run(debug=True)
