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

def retrieve_context(prompt, top_k=3):
    query_embedding = model.encode([prompt])
    D, I = index.search(np.array(query_embedding), top_k)
    retrieved = [documents[i] for i in I[0] if i < len(documents)]
    return "\n".join(retrieved)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_prompt = data.get("prompt", "")
    if not user_prompt:
        return Response("Missing prompt", status=400)

    # >>> RAG PHẦN NÀY <<<
    context = retrieve_context(user_prompt)
    combined_prompt = f"""You are an assistant. Use the following context to answer the question:
    
    Context:
    {context}

    Question: {user_prompt}
    Answer:"""

    def stream_response():
        payload = {
            "model": MODEL_NAME,
            "prompt": combined_prompt,
            "stream": True
        }
        try:
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
                if r.status_code != 200:
                    yield f"Error from Ollama: {r.status_code}"
                    return
                for line in r.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            chunk = data.get("response", "")
                            if chunk:
                                yield chunk
                        except Exception as decode_err:
                            yield f"[Decode error] {str(decode_err)}"
        except requests.exceptions.RequestException as req_err:
            yield f"Connection error: {str(req_err)}"

    return Response(stream_with_context(stream_response()), content_type='text/plain')
