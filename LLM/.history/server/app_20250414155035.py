from flask import Flask, request, stream_with_context, Response
from flask_cors import CORS
import requests
import json

# NEW: Import Chroma and embedding
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# --- Config ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"
CHROMA_DB_DIR = "chroma_db"

# --- Load Chroma Index ---
embedding_fn = OllamaEmbeddings(model=MODEL_NAME)
vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding_fn)

# --- Context Retrieval ---
def retrieve_context(query, top_k=4):
    docs = vectordb.similarity_search(query, k=top_k)
    return "\n---\n".join(doc.page_content for doc in docs)

# --- Chat API ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    context = retrieve_context(prompt)
    combined_prompt = f"""You are a helpful assistant specialized in mental health. Use the context below to answer:

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
    return "Flask RAG (ChromaDB + Ollama) is running."

if __name__ == "__main__":
    app.run(debug=True)
