from flask import Flask, request, stream_with_context, Response, jsonify
from flask_cors import CORS
import requests
import json
import cv2
import numpy as np
from ai2thor.controller import Controller
from io import BytesIO
from PIL import Image

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

# --- Initialize AI2Thor Controller ---
c = Controller()

# --- Context Retrieval ---
def retrieve_context(query, top_k=4):
    docs = vectordb.similarity_search(query, k=top_k)
    return "\n---\n".join(doc.page_content for doc in docs)

# --- AI2Thor Visualization --- 
def get_ai2thor_image():
    # Get the top-down camera image from AI2Thor
    event = c.step(action="GetMapViewCameraProperties")
    image = c.last_event.frame
    pil_image = Image.fromarray(image)
    
    # Convert to bytes
    img_byte_arr = BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    return img_byte_arr

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

# --- Visualization API for AI2Thor (direct call to Controller) ---
@app.route("/api/ai2thor_image", methods=["GET"])
def ai2thor_image():
    # Get AI2Thor image directly using the controller and stream it
    img_byte_arr = get_ai2thor_image()
    return Response(img_byte_arr, mimetype='image/png')

@app.route("/")
def home():
    return "Flask RAG (ChromaDB + Ollama + AI2Thor) is running."

if __name__ == "__main__":
    app.run(debug=True)



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



# from flask import Flask, request, stream_with_context, Response
# from flask_cors import CORS
# import requests
# import json

# from langchain_community.vectorstores import Chroma
# from langchain_ollama import OllamaEmbeddings

# # --- Flask App Setup ---
# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# # --- Config ---
# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"

# # --- Load Embedding and Chroma Collections ---
# embedding_fn = OllamaEmbeddings(model=MODEL_NAME)

# vectordb_emotional = Chroma(persist_directory="chroma_emotional", embedding_function=embedding_fn)
# vectordb_smarthome = Chroma(persist_directory="chroma_smarthome", embedding_function=embedding_fn)
# vectordb_healthcare = Chroma(persist_directory="chroma_healthcare", embedding_function=embedding_fn)

# # --- Robot Action Mapping ---
# ACTION_KEYWORDS = {
#     # Living Room
#     "turn on light": ["turn on the light", "switch on light", "lighting", "dark room"],
#     "play music": ["play music", "start music", "relaxing sound", "ambient sound"],
#     "turn on tv": ["turn on tv", "watch movie", "entertainment", "start television"],
#     "clean sofa": ["clean the sofa", "tidy up the couch", "remove dust", "sofa cleaning"],
#     "adjust temperature": ["lower temperature", "too hot", "too cold", "make it cooler", "adjust thermostat"],
#     "start air purifier": ["start air purifier", "clean the air", "dusty", "air quality", "filter air"],

#     # Bathroom
#     "turn on bathroom light": ["turn on bathroom light", "light up the bathroom", "dark bathroom"],
#     "warm up water": ["start water heater", "warm the shower", "hot water", "prepare bath"],
#     "clean bathroom": ["clean toilet", "clean the bathroom", "bathroom smells", "sanitize bathroom"],

#     # Bedroom
#     "turn on bedroom light": ["turn on bedroom light", "dim bedroom light", "bedroom dark"],
#     "prepare bed": ["make the bed", "prepare sleeping area", "bedtime setup"],
#     "play sleep sounds": ["play white noise", "sleep music", "soothing sound", "help me sleep"],
#     "adjust bedroom temperature": ["adjust bedroom temp", "too warm in bedroom", "cool down bedroom"],

#     # Kitchen
#     "turn on kitchen light": ["turn on kitchen light", "kitchen is dark"],
#     "boil water": ["boil water", "start kettle", "heat water"],
#     "preheat oven": ["preheat oven", "warm up the oven", "start cooking"],
#     "start coffee maker": ["make coffee", "brew coffee", "start coffee machine"],
#     "clean kitchen": ["clean kitchen", "sanitize kitchen", "dirty sink", "wipe countertop"]
# }

# def extract_actions_from_response(response_text):
#     tasks = []
#     lower_text = response_text.lower()
#     for action, keywords in ACTION_KEYWORDS.items():
#         if any(kw in lower_text for kw in keywords):
#             tasks.append(action)
#     return tasks

# # --- RAG: Multi-Intent Context Retrieval ---
# def retrieve_multi_context(query, top_k=2):
#     ctx_emotional = vectordb_emotional.similarity_search(query, k=top_k)
#     ctx_smarthome = vectordb_smarthome.similarity_search(query, k=top_k)
#     ctx_healthcare = vectordb_healthcare.similarity_search(query, k=top_k)

#     sections = [
#         ("[🧠 Emotional Support]", ctx_emotional),
#         ("[🏡 Smart Home Actions]", ctx_smarthome),
#         ("[💖 Health Advice]", ctx_healthcare)
#     ]
#     result = ""
#     for label, docs in sections:
#         if docs:
#             result += f"{label}\n" + "\n".join(doc.page_content for doc in docs) + "\n---\n"
#     return result

# # --- Chat API ---
# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return Response("Missing prompt", status=400)

#     context = retrieve_multi_context(prompt)
#     combined_prompt = f"""You are a helpful and empathetic smart home assistant.

# You understand emotions, suggest mental/health support, and can plan smart-home actions.
# Use the context below to assist the user:

# {context}

# User: {prompt}
# Assistant:"""

#     def stream_response():
#         payload = {
#             "model": MODEL_NAME,
#             "prompt": combined_prompt,
#             "stream": True
#         }
#         full_response = ""
#         try:
#             with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
#                 if r.status_code != 200:
#                     yield f"Error from Ollama: {r.status_code}"
#                     return
#                 for line in r.iter_lines():
#                     if line:
#                         try:
#                             data = json.loads(line.decode("utf-8"))
#                             chunk = data.get("response", "")
#                             full_response += chunk
#                             yield chunk
#                         except Exception as e:
#                             yield f"[Decode error] {str(e)}"
#             actions = extract_actions_from_response(full_response)
#             if actions:
#                 yield f"\n\n---\n[📋 Suggested Actions: {', '.join(actions)}]"
#         except Exception as e:
#             yield f"[Request error] {str(e)}"

#     return Response(stream_with_context(stream_response()), content_type='text/plain')

# @app.route("/")
# def home():
#     return "Flask RAG with Robot Action Planner is running."

# if __name__ == "__main__":
#     app.run(debug=True)
