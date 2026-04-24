import requests
import json
import logging
from flask import Flask, request, Response, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    return response

@app.route("/api/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    # Validate input
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    user_prompt = data.get("prompt", "").strip()
    
    if not user_prompt:
        return jsonify({"error": "Prompt cannot be empty"}), 400

    def generate():
        payload = {
            "model": OLLAMA_CONFIG["model"],
            "prompt": user_prompt,
            "stream": True,
            "options": {
                "temperature": 0.7
            }
        }
        
        try:
            with requests.post(
                OLLAMA_CONFIG["url"],
                json=payload,
                stream=True,
                timeout=OLLAMA_CONFIG["timeout"]
            ) as r:
                r.raise_for_status()  # Kiểm tra lỗi HTTP
                
                for line in r.iter_lines():
                    if line:
                        try:
                            part = json.loads(line.decode("utf-8"))
                            if "response" in part:
                                yield part["response"]
                            if part.get("done", False):
                                break
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Unexpected error: {e}")
                            yield "\n[ERROR] Failed to process response"
                            break
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama connection failed: {e}")
            yield "\n[ERROR] Service unavailable. Please try again later."

    return Response(
        stream_with_context(generate()),
        content_type='text/plain',
        headers={'X-Accel-Buffering': 'no'}  # Tắt buffering cho Nginx nếu có
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)