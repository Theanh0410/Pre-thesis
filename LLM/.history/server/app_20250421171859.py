# import os
# import json
# import requests
# import pandas as pd
# from flask import Flask, request, Response, stream_with_context, session
# from flask_cors import CORS
# from SmartHomeCommandExtractor import SmartHomeCommandExtractor
# from RAG.bm25 import BM25Retriever

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
# app.secret_key = 'your_secret_key'

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"
# LOG_FILE = 'conversation_log.txt'
# TASK_FILE = 'task.csv'

# # Load config
# with open("smarthome/actions.json") as f:
#     actions = json.load(f)
# with open("smarthome/synonyms.json") as f:
#     synonym_map = json.load(f)
# with open("smarthome/room_actions.json") as f:
#     room_actions = json.load(f)
# with open("smarthome/object_room_map.json") as f:
#     object_room_map = json.load(f)

# extractor = SmartHomeCommandExtractor(
#     actions=actions,
#     synonym_map=synonym_map,
#     room_actions=room_actions,
#     object_room_map=object_room_map,
#     threshold=0.3
# )

# bm25_retriever = BM25Retriever(docs_folder="documents")

# ROOM_ID_MAP = {
#     "living room": 201,
#     "kitchen": 1,
#     "bedroom": 301,
#     "bathroom": 401
# }

# # === Helper functions ===
# def write_to_txt(user_prompt, assistant_response, conversation_id):
#     with open(LOG_FILE, 'a', encoding='utf-8') as f:
#         f.write(f"ID: {conversation_id}\n")
#         f.write(f"User Prompt: {user_prompt}\n")
#         f.write(f"Assistant Response: {assistant_response}\n")
#         f.write('-' * 50 + '\n')

# def get_context():
#     return session.get('context', "")

# def update_context(user_prompt, assistant_response):
#     context = get_context()
#     session['context'] = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"

# def parse_user_feedback(user_input, original_actions):
#     user_input = user_input.lower()
#     result = {}
#     global_accept = any(kw in user_input for kw in ["all is good", "that's fine", "okay", "perfect", "go ahead"])
#     negative_phrases = ["i don't want", "except", "but not", "no need", "skip", "remove"]
#     for action in original_actions:
#         action = action.lower()
#         obj = action.split()[-1]
#         if any(neg in user_input and obj in user_input for neg in negative_phrases):
#             result[action] = "rejected"
#         elif f"only want the {obj}" in user_input or f"just the {obj}" in user_input:
#             result[action] = "confirmed"
#         elif global_accept:
#             result[action] = "confirmed"
#         else:
#             result[action] = "pending"
#     return result

# def save_tasks_to_csv(results):
#     if not os.path.exists(TASK_FILE) or os.stat(TASK_FILE).st_size == 0:
#         df_existing = pd.DataFrame()
#         current_id = 1
#     else:
#         df_existing = pd.read_csv(TASK_FILE)
#         if "ID" not in df_existing.columns or df_existing["ID"].dropna().empty:
#             current_id = 1
#         else:
#             current_id = int(df_existing["ID"].max()) + 1

#     new_rows = []
#     for r in results:
#         room_number = ROOM_ID_MAP.get(r["room"], "")
#         new_row = {
#             "ID": current_id,
#             "user_prompt": r["sentence"].strip(),
#             "RoomNumber": room_number,
#             "Object": r["object"] or "",
#             "Action": r["action"].lower(),
#             "Status": "not done",
#             "Agent_id": ""
#         }
#         new_rows.append(new_row)
#         current_id += 1

#     df_new = pd.DataFrame(new_rows)
#     if df_existing.empty:
#         df_new.to_csv(TASK_FILE, index=False)
#     else:
#         df_combined = pd.concat([df_existing, df_new], ignore_index=True)
#         df_combined.to_csv(TASK_FILE, index=False)

# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return Response("Missing prompt", status=400)

#     context = get_context()
#     bm25_context = "\n".join([doc for _, doc in bm25_retriever.get_top_k_filenames(prompt, k=5)])

#     combined_prompt = f"""
# You are a helpful assistant.
# Use the provided context to answer or act appropriately.

# Previous Dialog:
# {context}

# Relevant Documents:
# {bm25_context}

# User: {prompt}
# Assistant:"""

#     def stream_response():
#         payload = {
#             "model": MODEL_NAME,
#             "prompt": combined_prompt,
#             "stream": True
#         }

#         assistant_response = ""

#         try:
#             with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
#                 if r.status_code != 200:
#                     yield f"Error from Ollama: {r.status_code}"
#                     return
#                 for line in r.iter_lines():
#                     if line:
#                         try:
#                             data = json.loads(line.decode("utf-8"))
#                             assistant_response += data.get("response", "")
#                         except Exception as e:
#                             yield f"[Decode error] {str(e)}"

#             conversation_id = str(hash(f"{prompt}{assistant_response}"))
#             write_to_txt(prompt, assistant_response, conversation_id)
#             update_context(prompt, assistant_response)

#             if any(k in prompt.lower() for k in ["yes", "sure", "please simulate", "go ahead with simulation"]):
#                 suggested_results = extractor.extract(assistant_response)
#                 session['last_suggestions'] = [f"{r['action'].capitalize()} {r['object']}" for r in suggested_results if r['object']]
#                 suggested_actions = [f"{r['action'].lower()} {r['object']}" for r in suggested_results if r['object']]
#                 intent_result = parse_user_feedback(prompt, suggested_actions)
#                 confirmed_actions = [act for act, status in intent_result.items() if status == "confirmed"]
#                 if confirmed_actions:
#                     filtered_results = [
#                         r for r in suggested_results
#                         if f"{r['action'].lower()} {r['object']}" in confirmed_actions
#                     ]
#                     if filtered_results:
#                         save_tasks_to_csv(filtered_results)
#                         print(f"[Saved {len(filtered_results)} smart home tasks]")
#                 else:
#                     print("[No confirmed smart home actions detected.]")

#             yield assistant_response

#         except Exception as e:
#             yield f"[Request error] {str(e)}"

#     return Response(stream_with_context(stream_response()), content_type='text/plain')

# @app.route("/")
# def home():
#     return "Flask RAG + BM25 + SmartHomeCommandExtractor is running."

# if __name__ == "__main__":
#     if not os.path.exists(LOG_FILE):
#         with open(LOG_FILE, 'w', encoding='utf-8') as f:
#             f.write("Conversation Log:\n" + "=" * 50 + "\n")
#     app.run(debug=True)

import os
import json
import requests
import pandas as pd
from flask import Flask, request, Response, stream_with_context, session
from flask_cors import CORS
from SmartHomeCommandExtractor import SmartHomeCommandExtractor
from RAG.bm25 import BM25Retriever
from sentence_transformers import SentenceTransformer, util
import glob

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
app.secret_key = 'your_secret_key'

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"
LOG_FILE = 'conversation_log.txt'
TASK_FILE = 'task.csv'

# Load config
with open("smarthome/actions.json") as f:
    actions = json.load(f)
with open("smarthome/synonyms.json") as f:
    synonym_map = json.load(f)
with open("smarthome/room_actions.json") as f:
    room_actions = json.load(f)
with open("smarthome/object_room_map.json") as f:
    object_room_map = json.load(f)

# Extend config
extra_actions = ["Schedule", "Remind", "Lock", "Unlock", "Create scene", "Set mode"]
for act in extra_actions:
    if act not in actions:
        actions.append(act)

synonym_map.update({
    "plan": "Schedule",
    "set reminder": "Remind",
    "remind me": "Remind",
    "schedule": "Schedule",
    "add reminder": "Remind",
    "secure": "Lock",
    "unsecure": "Unlock",
    "create": "Create scene",
    "set scene": "Create scene",
    "eco mode": "Set mode",
    "night mode": "Set mode"
})

room_actions.setdefault("bedroom", []).extend(["Schedule wake up alarm", "Remind bedtime", "Set mode night"])
room_actions.setdefault("living room", []).extend(["Create scene goodnight", "Lock door", "Play soothing music"])
object_room_map.update({
    "alarm": "bedroom",
    "reminder": "bedroom",
    "scene": "living room",
    "door": "living room",
    "music": "living room",
    "mode": "bedroom"
})

extractor = SmartHomeCommandExtractor(
    actions=actions,
    synonym_map=synonym_map,
    room_actions=room_actions,
    object_room_map=object_room_map,
    threshold=0.3
)

bm25_retriever = BM25Retriever(docs_folder="documents")
vector_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

ROOM_ID_MAP = {
    "living room": 201,
    "kitchen": 1,
    "bedroom": 301,
    "bathroom": 401
}

# Vector search for context
vector_corpus = []
file_paths = glob.glob("documents/*.txt")
for file_path in file_paths:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
        vector_corpus.append((file_path, text))

corpus_texts = [txt for _, txt in vector_corpus]
corpus_embeddings = vector_model.encode(corpus_texts, convert_to_tensor=True)


def write_to_txt(user_prompt, assistant_response, conversation_id):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"ID: {conversation_id}\n")
        f.write(f"User Prompt: {user_prompt}\n")
        f.write(f"Assistant Response: {assistant_response}\n")
        f.write('-' * 50 + '\n')

def get_context():
    return session.get('context', "")

def update_context(user_prompt, assistant_response):
    context = get_context()
    session['context'] = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"

def parse_user_feedback(user_input, original_actions):
    user_input = user_input.lower()
    result = {}
    global_accept = any(kw in user_input for kw in ["all is good", "that's fine", "okay", "perfect", "go ahead"])
    negative_phrases = ["i don't want", "except", "but not", "no need", "skip", "remove"]
    for action in original_actions:
        action = action.lower()
        obj = action.split()[-1]
        if any(neg in user_input and obj in user_input for neg in negative_phrases):
            result[action] = "rejected"
        elif f"only want the {obj}" in user_input or f"just the {obj}" in user_input:
            result[action] = "confirmed"
        elif global_accept:
            result[action] = "confirmed"
        else:
            result[action] = "pending"
    return result

def save_tasks_to_csv(results):
    if not os.path.exists(TASK_FILE) or os.stat(TASK_FILE).st_size == 0:
        df_existing = pd.DataFrame()
        current_id = 1
    else:
        df_existing = pd.read_csv(TASK_FILE)
        if "ID" not in df_existing.columns or df_existing["ID"].dropna().empty:
            current_id = 1
        else:
            current_id = int(df_existing["ID"].max()) + 1

    new_rows = []
    for r in results:
        room_number = ROOM_ID_MAP.get(r["room"], "")
        new_row = {
            "ID": current_id,
            "user_prompt": r["sentence"].strip(),
            "RoomNumber": room_number,
            "Object": r["object"] or "",
            "Action": r["action"].lower(),
            "Status": "not done",
            "Agent_id": ""
        }
        new_rows.append(new_row)
        current_id += 1

    df_new = pd.DataFrame(new_rows)
    if df_existing.empty:
        df_new.to_csv(TASK_FILE, index=False)
    else:
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined.to_csv(TASK_FILE, index=False)

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    context = get_context()

    # Combine BM25 and vector search results
    bm25_context = [doc for _, doc in bm25_retriever.get_top_k_filenames(prompt, k=3)]
    query_embedding = vector_model.encode(prompt, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    top_results = cosine_scores.topk(2)
    vector_context = [corpus_texts[idx] for idx in top_results.indices.tolist()]

    all_context = bm25_context + vector_context
    combined_context = "\n".join(all_context)

    combined_prompt = f"""
You are a helpful assistant.
Use the provided context to answer or act appropriately.
Suggest a broader set of smart home actions that could help the user relax.

Previous Dialog:
{context}

Relevant Documents:
{combined_context}

User: {prompt}
Assistant:"""

    def stream_response():
        payload = {
            "model": MODEL_NAME,
            "prompt": combined_prompt,
            "stream": True
        }

        assistant_response = ""

        try:
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
                if r.status_code != 200:
                    yield f"Error from Ollama: {r.status_code}"
                    return
                for line in r.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            assistant_response += data.get("response", "")
                        except Exception as e:
                            yield f"[Decode error] {str(e)}"

            conversation_id = str(hash(f"{prompt}{assistant_response}"))
            write_to_txt(prompt, assistant_response, conversation_id)
            update_context(prompt, assistant_response)

            if any(k in prompt.lower() for k in ["yes", "sure", "please simulate", "go ahead with simulation"]):
                suggested_results = extractor.extract(assistant_response)
                session['last_suggestions'] = [f"{r['action'].capitalize()} {r['object']}" for r in suggested_results if r['object']]
                suggested_actions = [f"{r['action'].lower()} {r['object']}" for r in suggested_results if r['object']]
                intent_result = parse_user_feedback(prompt, suggested_actions)
                confirmed_actions = [act for act, status in intent_result.items() if status == "confirmed"]
                if confirmed_actions:
                    filtered_results = [
                        r for r in suggested_results
                        if f"{r['action'].lower()} {r['object']}" in confirmed_actions
                    ]
                    if filtered_results:
                        save_tasks_to_csv(filtered_results)
                        print(f"[Saved {len(filtered_results)} smart home tasks]")
                else:
                    print("[No confirmed smart home actions detected.]")

            yield assistant_response

        except Exception as e:
            yield f"[Request error] {str(e)}"

    return Response(stream_with_context(stream_response()), content_type='text/plain')

@app.route("/")
def home():
    return "Flask RAG + BM25 + Vector Search + SmartHomeCommandExtractor is running."

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write("Conversation Log:\n" + "=" * 50 + "\n")
    app.run(debug=True)

# import os
# import json
# import requests
# import pandas as pd
# import traceback
# import glob
# from flask import Flask, request, Response, stream_with_context, session, jsonify
# from flask_cors import CORS
# from SmartHomeCommandExtractor import SmartHomeCommandExtractor
# from RAG.bm25 import BM25Retriever
# from sentence_transformers import SentenceTransformer, util

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
# app.secret_key = 'your_secret_key'

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"
# LOG_FILE = 'conversation_log.txt'
# TASK_FILE = 'task.csv'

# # Load config
# with open("smarthome/actions.json") as f:
#     actions = json.load(f)
# with open("smarthome/synonyms.json") as f:
#     synonym_map = json.load(f)
# with open("smarthome/room_actions.json") as f:
#     room_actions = json.load(f)
# with open("smarthome/object_room_map.json") as f:
#     object_room_map = json.load(f)

# # Extend config
# extra_actions = ["Schedule", "Remind", "Lock", "Unlock", "Create scene", "Set mode"]
# for act in extra_actions:
#     if act not in actions:
#         actions.append(act)

# synonym_map.update({
#     "plan": "Schedule",
#     "set reminder": "Remind",
#     "remind me": "Remind",
#     "schedule": "Schedule",
#     "add reminder": "Remind",
#     "secure": "Lock",
#     "unsecure": "Unlock",
#     "create": "Create scene",
#     "set scene": "Create scene",
#     "eco mode": "Set mode",
#     "night mode": "Set mode"
# })

# room_actions.setdefault("bedroom", []).extend(["Schedule wake up alarm", "Remind bedtime", "Set mode night"])
# room_actions.setdefault("living room", []).extend(["Create scene goodnight", "Lock door", "Play soothing music"])
# object_room_map.update({
#     "alarm": "bedroom",
#     "reminder": "bedroom",
#     "scene": "living room",
#     "door": "living room",
#     "music": "living room",
#     "mode": "bedroom"
# })

# extractor = SmartHomeCommandExtractor(
#     actions=actions,
#     synonym_map=synonym_map,
#     room_actions=room_actions,
#     object_room_map=object_room_map,
#     threshold=0.3
# )

# bm25_retriever = BM25Retriever(docs_folder="documents")
# vector_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")

# ROOM_ID_MAP = {
#     "living room": 201,
#     "kitchen": 1,
#     "bedroom": 301,
#     "bathroom": 401
# }

# # Vector search for context
# vector_corpus = []
# file_paths = glob.glob("documents/*.txt")
# for file_path in file_paths:
#     with open(file_path, "r", encoding="utf-8") as f:
#         text = f.read()
#         vector_corpus.append((file_path, text))

# corpus_texts = [txt for _, txt in vector_corpus]
# corpus_embeddings = vector_model.encode(corpus_texts, convert_to_tensor=True)

# def write_to_txt(user_prompt, assistant_response, conversation_id):
#     with open(LOG_FILE, 'a', encoding='utf-8') as f:
#         f.write(f"ID: {conversation_id}\n")
#         f.write(f"User Prompt: {user_prompt}\n")
#         f.write(f"Assistant Response: {assistant_response}\n")
#         f.write('-' * 50 + '\n')

# def get_context():
#     return session.get('context', "")

# def update_context(user_prompt, assistant_response):
#     context = get_context()
#     session['context'] = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"

# def parse_user_feedback(user_input, original_actions):
#     user_input = user_input.lower()
#     result = {}
#     global_accept = any(kw in user_input for kw in ["all is good", "that's fine", "okay", "perfect", "go ahead"])
#     negative_phrases = ["i don't want", "except", "but not", "no need", "skip", "remove"]
#     for action in original_actions:
#         action = action.lower()
#         obj = action.split()[-1]
#         if any(neg in user_input and obj in user_input for neg in negative_phrases):
#             result[action] = "rejected"
#         elif f"only want the {obj}" in user_input or f"just the {obj}" in user_input:
#             result[action] = "confirmed"
#         elif global_accept:
#             result[action] = "confirmed"
#         else:
#             result[action] = "pending"
#     return result

# def save_tasks_to_csv(results):
#     if not os.path.exists(TASK_FILE) or os.stat(TASK_FILE).st_size == 0:
#         df_existing = pd.DataFrame()
#         current_id = 1
#     else:
#         df_existing = pd.read_csv(TASK_FILE)
#         if "ID" not in df_existing.columns or df_existing["ID"].dropna().empty:
#             current_id = 1
#         else:
#             current_id = int(df_existing["ID"].max()) + 1

#     new_rows = []
#     for r in results:
#         room_number = ROOM_ID_MAP.get(r["room"], "")
#         new_row = {
#             "ID": current_id,
#             "user_prompt": r["sentence"].strip(),
#             "RoomNumber": room_number,
#             "Object": r["object"] or "",
#             "Action": r["action"].lower(),
#             "Status": "not done",
#             "Agent_id": ""
#         }
#         new_rows.append(new_row)
#         current_id += 1

#     df_new = pd.DataFrame(new_rows)
#     if df_existing.empty:
#         df_new.to_csv(TASK_FILE, index=False)
#     else:
#         df_combined = pd.concat([df_existing, df_new], ignore_index=True)
#         df_combined.to_csv(TASK_FILE, index=False)

# @app.route("/api/chat", methods=["POST"])
# def chat():
#     try:
#         data = request.json
#         prompt = data.get("prompt", "").strip()
#         if not prompt:
#             return jsonify({"error": "Missing prompt"}), 400

#         context = get_context()

#         bm25_context = [doc for _, doc in bm25_retriever.get_top_k_filenames(prompt, k=3)]
#         query_embedding = vector_model.encode(prompt, convert_to_tensor=True)
#         cosine_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
#         top_results = cosine_scores.topk(2)
#         top_indices = top_results.indices.tolist()
#         vector_context = [corpus_texts[idx] for idx in top_indices] if top_indices else []

#         all_context = bm25_context + vector_context
#         combined_context = "\n".join(all_context)

#         combined_prompt = f"""
# You are a helpful assistant.
# Use the provided context to answer or act appropriately.
# Suggest a broader set of smart home actions that could help the user relax.

# Previous Dialog:
# {context}

# Relevant Documents:
# {combined_context}

# User: {prompt}
# Assistant:"""

#         def stream_response():
#             payload = {
#                 "model": MODEL_NAME,
#                 "prompt": combined_prompt,
#                 "stream": True
#             }
#             assistant_response = ""

#             try:
#                 with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
#                     if r.status_code != 200:
#                         yield f"Error from Ollama: {r.status_code}"
#                         return
#                     for line in r.iter_lines():
#                         if line:
#                             try:
#                                 data = json.loads(line.decode("utf-8"))
#                                 assistant_response += data.get("response", "")
#                             except Exception as e:
#                                 yield f"[Decode error] {str(e)}"

#                 conversation_id = str(hash(f"{prompt}{assistant_response}"))
#                 write_to_txt(prompt, assistant_response, conversation_id)
#                 update_context(prompt, assistant_response)

#                 if any(k in prompt.lower() for k in ["yes", "sure", "please simulate", "go ahead with simulation"]):
#                     suggested_results = extractor.extract(assistant_response)
#                     session['last_suggestions'] = [f"{r['action'].capitalize()} {r['object']}" for r in suggested_results if r['object']]
#                     suggested_actions = [f"{r['action'].lower()} {r['object']}" for r in suggested_results if r['object']]
#                     intent_result = parse_user_feedback(prompt, suggested_actions)
#                     confirmed_actions = [act for act, status in intent_result.items() if status == "confirmed"]
#                     if confirmed_actions:
#                         filtered_results = [
#                             r for r in suggested_results
#                             if f"{r['action'].lower()} {r['object']}" in confirmed_actions
#                         ]
#                         if filtered_results:
#                             save_tasks_to_csv(filtered_results)
#                             print(f"[Saved {len(filtered_results)} smart home tasks]")
#                     else:
#                         print("[No confirmed smart home actions detected.]")

#                 yield assistant_response

#             except Exception as e:
#                 error_message = f"[Request error] {str(e)}\n{traceback.format_exc()}"
#                 write_to_txt(prompt, error_message, str(hash(prompt)))
#                 yield error_message

#         return Response(stream_with_context(stream_response()), content_type='text/plain')

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @app.route("/")
# def home():
#     return "Flask RAG + BM25 + Vector Search + SmartHomeCommandExtractor is running."

# if __name__ == "__main__":
#     if not os.path.exists(LOG_FILE):
#         with open(LOG_FILE, 'w', encoding='utf-8') as f:
#             f.write("Conversation Log:\n" + "=" * 50 + "\n")
#     app.run(debug=True)
