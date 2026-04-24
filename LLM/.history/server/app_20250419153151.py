# from flask import Flask, request, stream_with_context, Response
# from flask_cors import CORS
# import requests
# import json

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# # Config
# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"

# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return Response("Missing prompt", status=400)

#     # Directly use the user's prompt to generate the combined prompt
#     combined_prompt = f"""You are a helpful assistant. You understand emotions, suggest mental/health support, and can plan smart-home actions Use the context to answer:

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
#     return "✅ Flask RAG + Ollama is running."

# if __name__ == "__main__":
#     app.run(debug=True)


# from flask import Flask, request, stream_with_context, Response, session
# from flask_cors import CORS
# import requests
# import json

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# # Secret key for session management
# app.secret_key = 'your_secret_key'

# # Config
# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"

# # --- Context Management ---
# def get_context():
#     """Retrieve the current context from the session"""
#     return session.get('context', "")

# def update_context(user_prompt, assistant_response):
#     """Update the session context with user input and assistant response"""
#     context = get_context()
#     new_context = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"
#     session['context'] = new_context

# def save_actions(actions):
#     """Save the actions chosen by the user into session"""
#     session['actions'] = actions

# def get_actions():
#     """Retrieve saved actions from the session"""
#     return session.get('actions', [])

# # --- Chat API ---
# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return Response("Missing prompt", status=400)

#     # Retrieve previous context
#     context = get_context()

#     # Create a combined prompt with previous context and the user's current prompt
#     combined_prompt = f"""You are a helpful assistant. You understand emotions, suggest mental/health support, and can plan smart-home actions. Use the context to answer:

# Previous Context:
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
#                             assistant_response = data.get("response", "")
#                             yield assistant_response

#                             # Update context with the latest assistant response
#                             update_context(prompt, assistant_response)

#                             # If the user mentioned "5 actions", provide a summary of the actions
#                             if "5 actions" in prompt.lower():
#                                 actions = get_actions()
#                                 action_summary = ", ".join(actions)  # Create a summary of the actions
#                                 yield f"Here's a summary of the actions you selected: {action_summary}"
#                         except Exception as e:
#                             yield f"[Decode error] {str(e)}"
#         except Exception as e:
#             yield f"[Request error] {str(e)}"

#     return Response(stream_with_context(stream_response()), content_type='text/plain')

# @app.route("/")
# def home():
#     return "✅ Flask RAG + Ollama is running."

# if __name__ == "__main__":
#     app.run(debug=True)


# import csv
# from flask import Flask, request, stream_with_context, Response, session
# from flask_cors import CORS
# import requests
# import json

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# # Secret key for session management
# app.secret_key = 'your_secret_key'

# # Config
# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"

# # --- Helper Function to Write to CSV ---
# def write_to_csv(user_prompt, actions):
#     """Write the user prompt and actions to a CSV file."""
#     file_path = './action_log.csv'

#     # Define CSV header
#     fieldnames = ['ID', 'user_prompt', 'RoomNumber', 'Object', 'Action', 'Status', 'Agent_id']
    
#     # Check if the file exists to decide whether to write header or not
#     file_exists = False
#     try:
#         with open(file_path, 'r'):
#             file_exists = True
#     except FileNotFoundError:
#         file_exists = False
    
#     with open(file_path, mode='a', newline='', encoding='utf-8') as file:
#         writer = csv.DictWriter(file, fieldnames=fieldnames)
        
#         if not file_exists:
#             writer.writeheader()  # Write header only if file doesn't exist
        
#         # Iterate over each action and log them
#         for idx, action in enumerate(actions):
#             writer.writerow({
#                 'ID': idx + 1,  # Simple incrementing ID
#                 'user_prompt': user_prompt,
#                 'RoomNumber': "",  # Room number, can be dynamic if needed
#                 'Object': action.split()[0],  # Assumes action has object as the first word
#                 'Action': action.split()[1],  # Assumes action type (e.g., turnOn, play, etc.)
#                 'Status': 'not done',  # Status set to done, can be modified dynamically
#                 'Agent_id': ""  # Static agent ID, could be dynamic if multiple agents
#             })

# # --- Context Management ---
# def get_context():
#     """Retrieve the current context from the session"""
#     return session.get('context', "")

# def update_context(user_prompt, assistant_response):
#     """Update the session context with user input and assistant response"""
#     context = get_context()
#     new_context = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"
#     session['context'] = new_context

# # --- Chat API ---
# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     prompt = data.get("prompt", "").strip()
#     if not prompt:
#         return Response("Missing prompt", status=400)

#     # Retrieve previous context
#     context = get_context()

#     # Create a combined prompt with previous context and the user's current prompt
#     combined_prompt = f"""You are a helpful assistant. You understand emotions, suggest mental/health support, and can plan smart-home actions. Use the context to answer:

# Previous Context:
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
#                             assistant_response = data.get("response", "")
#                             yield assistant_response

#                             # Update context with the latest assistant response
#                             update_context(prompt, assistant_response)

#                             # If the user mentioned "5 actions", provide a summary of the actions
#                             if "5 actions" in prompt.lower():
#                                 actions = ["Turn on the lights in the living room", 
#                                            "Adjust the thermostat", 
#                                            "Play some music", 
#                                            "Dim the smart bulbs", 
#                                            "Open the windows"]
#                                 write_to_csv(prompt, actions)  # Write to CSV file
#                                 action_summary = ", ".join(actions)  # Create a summary of the actions
#                                 yield f"Here's a summary of the actions you selected: {action_summary}"
#                         except Exception as e:
#                             yield f"[Decode error] {str(e)}"
#         except Exception as e:
#             yield f"[Request error] {str(e)}"

#     return Response(stream_with_context(stream_response()), content_type='text/plain')

# @app.route("/")
# def home():
#     return "Flask RAG + Ollama is running."

# if __name__ == "__main__":
#     app.run(debug=True)


import csv
from flask import Flask, request, stream_with_context, Response, session
from flask_cors import CORS
import requests
import json
import os
from ../SmartHomeCommandExtractor import SmartHomeCommandExtractor
import pandas as pd

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"
LOG_FILE = 'conversation_log.txt'
TASK_FILE = 'task.csv'

# === Load SmartHome Config ===
with open("actions.json") as f:
    actions = json.load(f)
with open("synonyms.json") as f:
    synonym_map = json.load(f)
with open("room_actions.json") as f:
    room_actions = json.load(f)
with open("object_room_map.json") as f:
    object_room_map = json.load(f)


extractor = SmartHomeCommandExtractor(
    actions=actions,
    synonym_map=synonym_map,
    room_actions=room_actions,
    object_room_map=object_room_map,
    threshold=0.3
)

ROOM_ID_MAP = {
    "living room": 201,
    "kitchen": 1,
    "bedroom": 301,
    "bathroom": 401
}

# === Helpers ===
def write_to_txt(user_prompt, assistant_response, conversation_id):
    with open(LOG_FILE, 'a', encoding='utf-8') as file:
        file.write(f"ID: {conversation_id}\n")
        file.write(f"User Prompt: {user_prompt}\n")
        file.write(f"Assistant Response: {assistant_response}\n")
        file.write('-' * 50 + '\n')

def get_context():
    return session.get('context', "")

def update_context(user_prompt, assistant_response):
    context = get_context()
    new_context = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"
    session['context'] = new_context

def extract_smart_actions_from_text(text):
    actions = []
    keywords = ["turn on", "turn off", "adjust", "prepare", "play", "open", "close"]
    objects = ["light", "music", "thermostat", "drink", "curtain", "tv", "coffee"]
    for line in text.split("\n"):
        line = line.strip().lower()
        for kw in keywords:
            for obj in objects:
                if kw in line and obj in line:
                    actions.append(f"{kw} {obj}")
    return list(set(actions))

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

# === Main Chat Endpoint ===
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    context = get_context()

    combined_prompt = f"""You are a helpful assistant. You understand emotions, suggest mental/health support, and can plan smart-home actions. Use the context to answer:

Previous Context:
{context}

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

            # === Smart Home Filtering ===
            suggested_actions = extract_smart_actions_from_text(assistant_response)
            intent_result = parse_user_feedback(prompt, suggested_actions)
            confirmed_actions = [act for act, status in intent_result.items() if status == "confirmed"]

            if confirmed_actions:
                extracted_results = extractor.extract(assistant_response)
                filtered_results = [
                    r for r in extracted_results
                    if f"{r['action'].lower()} {r['object']}" in confirmed_actions
                ]
                if filtered_results:
                    save_tasks_to_csv(filtered_results)
                    print(f"[✅ Saved {len(filtered_results)} smart home tasks]")
            else:
                print("[⛔ No confirmed smart home actions detected.]")

            yield assistant_response

        except Exception as e:
            yield f"[Request error] {str(e)}"

    return Response(stream_with_context(stream_response()), content_type='text/plain')

@app.route("/")
def home():
    return "Flask RAG + Ollama is running."

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'w', encoding='utf-8') as file:
            file.write("Conversation Log:\n")
            file.write("=" * 50 + "\n")
    app.run(debug=True)