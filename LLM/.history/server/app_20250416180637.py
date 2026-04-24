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


from flask import Flask, request, stream_with_context, Response, session
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# Secret key for session management
app.secret_key = 'your_secret_key'

# Config
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# --- Context Management ---
def get_context():
    """Retrieve the current context from the session"""
    return session.get('context', "")

def update_context(user_prompt, assistant_response):
    """Update the session context with user input and assistant response"""
    context = get_context()
    new_context = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"
    session['context'] = new_context

def save_actions(actions):
    """Save the actions chosen by the user into session"""
    session['actions'] = actions

def get_actions():
    """Retrieve saved actions from the session"""
    return session.get('actions', [])

# --- Chat API ---
@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    # Retrieve previous context
    context = get_context()

    # Create a combined prompt with previous context and the user's current prompt
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
        try:
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=120) as r:
                if r.status_code != 200:
                    yield f"Error from Ollama: {r.status_code}"
                    return
                for line in r.iter_lines():
                    if line:
                        try:
                            data = json.loads(line.decode("utf-8"))
                            assistant_response = data.get("response", "")
                            yield assistant_response

                            # Update context with the latest assistant response
                            update_context(prompt, assistant_response)

                            # If the user mentioned "5 actions", provide a summary of the actions
                            if "5 actions" in prompt.lower():
                                actions = get_actions()
                                action_summary = ", ".join(actions)  # Create a summary of the actions
                                yield f"Here's a summary of the actions you selected: {action_summary}"
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
