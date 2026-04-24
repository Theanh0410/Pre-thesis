# from flask import Flask, request, stream_with_context, Response
# from flask_cors import CORS
# import requests
# import json

# # NEW: Import Chroma and embedding
# from langchain_community.vectorstores import Chroma
# from langchain_ollama import OllamaEmbeddings

# # --- Flask App Setup ---
# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# # --- Config ---
# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"
# CHROMA_DB_DIR = "chroma_db"

# # --- Load Chroma Index ---
# embedding_fn = OllamaEmbeddings(model=MODEL_NAME)
# vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding_fn)

# # --- Context Retrieval ---
# def retrieve_context(query, top_k=4):
#     docs = vectordb.similarity_search(query, k=top_k)
#     return "\n---\n".join(doc.page_content for doc in docs)

# # --- Chat API ---
# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return Response("Missing prompt", status=400)

#     context = retrieve_context(prompt)
#     combined_prompt = f"""You are a helpful assistant specialized in mental health. Use the context below to answer:

# Context:
# {context}

# User: {prompt}
# Assistant:"""

#     def stream_response():
#         payload = {
#             "model": MODEL_NAME,
#             "prompt": combined_prompt,
#             "stream": True
#         }
#         try:
#             with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
#                 if r.status_code != 200:
#                     yield f"Error from Ollama: {r.status_code}"
#                     return
#                 for line in r.iter_lines():
#                     if line:
#                         try:
#                             data = json.loads(line.decode("utf-8"))
#                             yield data.get("response", "")
#                         except Exception as e:
#                             yield f"[Decode error] {str(e)}"
#         except Exception as e:
#             yield f"[Request error] {str(e)}"

#     return Response(stream_with_context(stream_response()), content_type='text/plain')

# @app.route("/")
# def home():
#     return "Flask RAG (ChromaDB + Ollama) is running."

# if __name__ == "__main__":
#     app.run(debug=True)



from flask import Flask, request, stream_with_context, Response
from flask_cors import CORS
import requests
import json

from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# --- Config ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# --- Load Embedding and Chroma Collections ---
embedding_fn = OllamaEmbeddings(model=MODEL_NAME)

vectordb_emotional = Chroma(persist_directory="chroma_emotional", embedding_function=embedding_fn)
vectordb_smarthome = Chroma(persist_directory="chroma_smarthome", embedding_function=embedding_fn)
vectordb_healthcare = Chroma(persist_directory="chroma_healthcare", embedding_function=embedding_fn)

# --- Robot Action Mapping ---
ACTION_KEYWORDS = {
    "turn on light": ["bật đèn", "mở đèn", "chiếu sáng", "phòng tối"],
    "play music": ["mở nhạc", "phát nhạc", "âm thanh thư giãn"],
    "turn on tv": ["bật tivi", "xem phim", "giải trí"],
    "clean sofa": ["dọn dẹp", "sofa", "ghế", "lau dọn"],
    "adjust temperature": ["giảm nhiệt", "nóng", "lạnh", "mát hơn"],
    "start air purifier": ["lọc khí", "không khí", "bụi", "nghẹt mũi"]
}

def extract_actions_from_response(response_text):
    tasks = []
    lower_text = response_text.lower()
    for action, keywords in ACTION_KEYWORDS.items():
        if any(kw in lower_text for kw in keywords):
            tasks.append(action)
    return tasks

# --- RAG: Multi-Intent Context Retrieval ---
def retrieve_multi_context(query, top_k=2):
    ctx_emotional = vectordb_emotional.similarity_search(query, k=top_k)
    ctx_smarthome = vectordb_smarthome.similarity_search(query, k=top_k)
    ctx_healthcare = vectordb_healthcare.similarity_search(query, k=top_k)

    sections = [
        ("[🧠 Emotional Support]", ctx_emotional),
        ("[🏡 Smart Home Actions]", ctx_smarthome),
        ("[💖 Health Advice]", ctx_healthcare)
    ]
    result = ""
    for label, docs in sections:
        if docs:
            result += f"{label}\n" + "\n".join(doc.page_content for doc in docs) + "\n---\n"
    return result

# --- Chat API ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    context = retrieve_multi_context(prompt)
    combined_prompt = f"""You are a helpful and empathetic smart home assistant.

You understand emotions, suggest mental/health support, and can plan smart-home actions.
Use the context below to assist the user:

{context}

User: {prompt}
Assistant:"""

    def stream_response():
        payload = {
            "model": MODEL_NAME,
            "prompt": combined_prompt,
            "stream": True
        }
        full_response = ""
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
                            full_response += chunk
                            yield chunk
                        except Exception as e:
                            yield f"[Decode error] {str(e)}"
            actions = extract_actions_from_response(full_response)
            if actions:
                yield f"\n\n---\n[📋 Suggested Actions: {', '.join(actions)}]"
        except Exception as e:
            yield f"[Request error] {str(e)}"

    return Response(stream_with_context(stream_response()), content_type='text/plain')

@app.route("/")
def home():
    return "Flask RAG with Robot Action Planner is running."

if __name__ == "__main__":
    app.run(debug=True)
