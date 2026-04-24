from flask import Flask, request, jsonify, stream_with_context, Response
from flask_cors import CORS
import requests
import json
import logging

app = Flask(__name__)
CORS(app)  # Mở rộng CORS cho tất cả routes

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config có thể tùy chỉnh
OLLAMA_CONFIG = {
    "url": "http://localhost:11434/api/generate",
    "model": "llama3",
    "timeout": 30  # timeout (giây)
}

@app.route("/api/chat", methods=["POST"])
def chat():
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