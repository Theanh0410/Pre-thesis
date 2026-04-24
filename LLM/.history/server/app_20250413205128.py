from flask import Flask, request, stream_with_context, Response
from flask_cors import CORS
import requests
import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# === LOAD RAG INDEX ===
model = SentenceTransformer("all-MiniLM-L6-v2")  # Hoặc bất kỳ sentence embedding nào
index = faiss.read_index("rag_index.faiss")  # FAISS index
with open("documents.json", "r") as f:
    documents = json.load(f)  # List of texts, ví dụ: ["Văn bản 1", "Văn bản 2", ...]
