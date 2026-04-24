from flask import Flask, request, stream_with_context, Response
from flask_cors import CORS
import requests
import json
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# Config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# Load index
model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("rag_index.faiss")
with open("documents.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

def retrieve_context(query, top_k=3):
    q_vec = model.encode([query])
    D, I = index.search(np.array(q_vec), top_k)
    return "\n---\n".join(chunks[i] for i in I[0] if i < len(chunks))

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    context = retrieve_context(prompt)
    combined_prompt = f"""You are a helpful assistant. Use the context to answer:

Context:
{context}

User: {prompt}
Assistant:"""

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
                            yield data.get("response", "")
                        except Exception as e:
                            yield f"[Decode error] {str(e)}"
        except Exception as e:
            yield f"[Request error] {str(e)}"

    return Response(stream_with_context(stream_response()), content_type='text/plain')

@app.route("/")
def home():
    return "✅ Flask RAG + Ollama is running."

if __name__ == "__main__":
    app.run(debug=True)
