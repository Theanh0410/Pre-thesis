from flask import Flask, request, jsonify, stream_with_context, Response
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    user_prompt = data.get("prompt", "")

    def generate():
        payload = {
            "model": MODEL_NAME,
            "prompt": user_prompt,
            "stream": True
        }
        with requests.post(OLLAMA_URL, json=payload, stream=True) as r:
            print("[Ollama Status]", r.status_code)
            print("[Ollama Raw Response]", r.text)
            for line in r.iter_lines():
                if line:
                    try:
                        part = json.loads(line.decode("utf-8"))
                        chunk = part.get("response", "")
                        if chunk:
                            yield chunk
                    except Exception as e:
                        print("[Decode Error]", e)
                        continue
    return Response(stream_with_context(generate()), content_type='text/plain')

if __name__ == "__main__":
    app.run(debug=True)