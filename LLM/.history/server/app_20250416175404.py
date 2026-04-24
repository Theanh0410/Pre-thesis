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

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return Response("Missing prompt", status=400)

    # Retrieve context from session if exists, else start a new context
    context = session.get('context', "")
    
    # Combine context with new user prompt
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
                            
                            # Update context in session with the latest assistant response
                            session['context'] = f"{context}\nUser: {prompt}\nAssistant: {assistant_response}"
                        except Exception as e:
                            yield f"[Decode error] {str(e)}"
        except Exception as e:
            yield f"[Request error] {str(e)}"

    return Response(stream_with_context(stream_response()), content_type='text/plain')

@app.route("/")
def home():
    return "Flask RAG + Ollama is running."

if __name__ == "__main__":
    app.run(debug=True)
