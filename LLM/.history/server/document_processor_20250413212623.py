# from flask import Flask, request, stream_with_context, Response
# from flask_cors import CORS
# import requests
# import json

# app = Flask(__name__)
# CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

# OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"

# @app.route("/api/chat", methods=["POST"])
# def chat():
#     data = request.json
#     user_prompt = data.get("prompt", "")
#     if not user_prompt:
#         return Response("Missing prompt", status=400)

#     def stream_response():
#         payload = {
#             "model": MODEL_NAME,
#             "prompt": user_prompt,
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
#                             chunk = data.get("response", "")
#                             if chunk:
#                                 yield chunk
#                         except Exception as decode_err:
#                             yield f"[Decode error] {str(decode_err)}"
#         except requests.exceptions.RequestException as req_err:
#             yield f"Connection error: {str(req_err)}"

#     return Response(stream_with_context(stream_response()), content_type='text/plain')

# @app.route("/")
# def home():
#     return "✅ Flask Ollama Chat API is running."

# if __name__ == "__main__":
#     app.run(debug=True)
