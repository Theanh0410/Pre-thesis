import os
import json
import requests
import pandas as pd
import time
import threading
from flask import Flask, jsonify, session
from flask_cors import CORS
from SmartHomeCommandExtractor import SmartHomeCommandExtractor
from ContextualCommandProcessor import ContextualCommandProcessor
from RAG.bm25 import BM25Retriever

# Import speech to text functionality
import wave
import numpy as np
from vosk import Model, KaldiRecognizer
import sounddevice as sd

# Import ThingSpeak functionality
import logging

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
app.secret_key = 'your_secret_key'

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"
LOG_FILE = 'conversation_log.txt'
TASK_FILE = os.path.join(os.path.dirname(__file__), "caregiver_command.csv")
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "vosk-model-en-us-0.22")
vosk_model = Model(VOSK_MODEL_PATH)
# THINGSPEAK_API_KEY = "B8MGA7B6J96EXBG2"

import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "theanh0410.cloud.shiftr.io"
MQTT_PORT = 1883
MQTT_USERNAME = "theanh0410"
MQTT_PASSWORD = "eoCNam4gR2IWOA6d"
MQTT_TOPIC = "home/control"

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

def publish_to_shiftr(command_data):
    payload = json.dumps(command_data)
    result = mqtt_client.publish(MQTT_TOPIC, payload)
    return result.rc == 0

# ThingSpeak logging setup
logging.basicConfig(
    filename="thingspeak_integration.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load config
with open("smarthome/actions.json") as f:
    actions = json.load(f)
with open("smarthome/synonyms.json") as f:
    synonym_map = json.load(f)
with open("smarthome/room_actions.json") as f:
    room_actions = json.load(f)
with open("smarthome/object_room_map.json") as f:
    object_room_map = json.load(f)

extractor = SmartHomeCommandExtractor(
    actions=actions,
    synonym_map=synonym_map,
    room_actions=room_actions,
    object_room_map=object_room_map,
    threshold=0.1
)

contextual_processor = ContextualCommandProcessor(
    room_actions=room_actions,
    object_room_map=object_room_map
)

bm25_retriever = BM25Retriever(docs_folder="documents")

ROOM_ID_MAP = {
    "living room": 201,
    "kitchen": 1,
    "bedroom": 301,
    "bathroom": 401
}

# === Speech to Text Function ===
# def speech_to_text(timeout=6, sample_rate=16000):
#     try:
#         recognizer = KaldiRecognizer(vosk_model, sample_rate)

#         print(f"Please say something that I can help you...")
#         audio = sd.rec(int(timeout * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
#         sd.wait()

#         # Convert audio to bytes
#         audio_data = audio.tobytes()

#         # Speech recognition
#         recognizer.AcceptWaveform(audio_data)
#         result = json.loads(recognizer.Result())
#         text = result.get("text", "")

#         # Clean up memory
#         del recognizer
#         # del model
#         import gc
#         gc.collect()

#         return text

#     except Exception as e:
#         print(f"Error in speech_to_text: {e}")
#         return ""
    
def speech_to_text(timeout=6, sample_rate=16000, silence_threshold=1):
    try:
        recognizer = KaldiRecognizer(vosk_model, sample_rate)
        
        print(f"Please say something that I can help you...")
        
        audio_data = []
        start_time = time.time()

        # Continuously record and append audio data until silence is detected
        while True:
            audio = sd.rec(int(timeout * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()

            # Convert audio to bytes and add to audio_data
            audio_data.extend(audio.tobytes())
            
            # Check silence (if last chunk is silent for "silence_threshold" seconds)
            if len(audio_data) > 0 and time.time() - start_time > silence_threshold:
                break  # Stop recording after silence threshold

        # Process the accumulated audio data
        recognizer.AcceptWaveform(bytes(audio_data))
        result = json.loads(recognizer.Result())
        text = result.get("text", "")

        # Clean up memory
        del recognizer
        import gc
        gc.collect()

        return text

    except Exception as e:
        print(f"Error in speech_to_text: {e}")
        return ""

# === ThingSpeak Upload Function ===
# def upload_to_thingspeak(thingspeak_data, api_key):
#     object_map = {"light": 1, "fan": 2}  
#     action_map = {"Turn on": 1, "Turn off": 0} 
    
#     object_value = object_map.get(thingspeak_data["device"], 0)
#     action_value = action_map.get(thingspeak_data["action"], 0)
    
#     params = {
#         "api_key": api_key,
#         "field1": object_value,
#         "field2": action_value,
#     }
#     response = requests.get("https://api.thingspeak.com/update", params=params)
#     print(f"ThingSpeak response: {response.status_code}, {response.text}")
#     return response.status_code == 200

# Global context for voice assistant (when not using Flask session)
VOICE_CONTEXT = ""

# === Helper functions ===
def write_to_txt(user_prompt, assistant_response, conversation_id):
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"ID: {conversation_id}\n")
        f.write(f"User Prompt: {user_prompt}\n")
        f.write(f"Assistant Response: {assistant_response}\n")
        f.write('-' * 50 + '\n')

def get_context(use_flask_session=True):
    if use_flask_session:
        try:
            return session.get('context', "")
        except RuntimeError:
            # Outside of request context, use global context
            return VOICE_CONTEXT
    else:
        return VOICE_CONTEXT

def update_context(user_prompt, assistant_response, use_flask_session=True):
    global VOICE_CONTEXT
    context = get_context(use_flask_session)
    new_context = f"{context}\nUser: {user_prompt}\nAssistant: {assistant_response}"
    
    if use_flask_session:
        try:
            session['context'] = new_context
        except RuntimeError:
            # Outside of request context, use global context
            VOICE_CONTEXT = new_context
    else:
        VOICE_CONTEXT = new_context

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
        # Handle both dict results and ensure proper types
        if not isinstance(r, dict):
            print(f"Warning: Skipping non-dict result: {r}")
            continue
            
        # Get fields with defaults
        room = r.get("room", "living room")
        sentence = r.get("sentence", "")
        device = r.get("object") or r.get("device", "unknown")
        action = r.get("action", "unknown")
        
        # Ensure types are correct
        if not isinstance(sentence, str):
            sentence = str(sentence)
        if not isinstance(room, str):
            room = str(room)
        if not isinstance(device, str):
            device = str(device)
        if not isinstance(action, str):
            action = str(action)
        
        room_number = ROOM_ID_MAP.get(room, "")
        new_row = {
            "ID": current_id,
            "user_prompt": sentence.strip(),
            "RoomNumber": room_number,
            "Object": device,
            "Action": action.lower(),
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

def is_device_control_command(results):
    device_keywords = ["light", "fan", "lamp", "bulb", "switch"]
    action_keywords = ["turn on", "turn off", "switch on", "switch off", "open", "close"]
    
    for result in results:
        # Skip non-dict results
        if not isinstance(result, dict):
            continue
            
        obj = result.get("object") or result.get("device", "")
        action = result.get("action", "")
        
        # Ensure we have strings
        if not isinstance(obj, str) or not isinstance(action, str):
            continue
            
        obj_lower = obj.lower()
        action_lower = action.lower()
        
        if any(device in obj_lower for device in device_keywords) and any(act in action_lower for act in action_keywords):
            return True
    return False

def process_one_voice_command():
    """Process one voice input and return result for web/API use"""
    try:
        # Get speech input
        prompt = speech_to_text(timeout=6)

        if not prompt.strip():
            return {
                "status": "error",
                "message": "No speech detected",
                "text": "",
                "response": "",
                "smart_home": []
            }

        print(f"\n🎤 Voice Input: {prompt}")

        # Process with AI
        context = get_context(use_flask_session=False)
        bm25_context = "\n".join([doc for _, doc in bm25_retriever.get_top_k_filenames(prompt, k=5)])

        combined_prompt = f"""
        
        You are a helpful assistant.
        Use the provided context to answer or act appropriately.

        Previous Dialog:
        {context}

        Relevant Documents:
        {bm25_context}

        User: {prompt}
        Assistant:"""

        payload = {
            "model": MODEL_NAME,
            "prompt": combined_prompt,
            "stream": False
        }

        assistant_response = ""

        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                assistant_response = data.get("response", "")
            else:
                assistant_response = f"Error from Ollama: {response.status_code}"

        except Exception as e:
            assistant_response = f"Request error: {str(e)}"

        # Log conversation
        conversation_id = str(hash(f"{prompt}{assistant_response}"))
        write_to_txt(prompt, assistant_response, conversation_id)
        update_context(prompt, assistant_response, use_flask_session=False)

        # Extract smart home commands
        # Step 1: Try contextual processor first (comfort/emotional states)
        contextual_results = contextual_processor.process_contextual_command(prompt)
        
        if contextual_results and len(contextual_results) > 0 and contextual_results[0].get("valid"):
            # High confidence contextual match - use this
            suggested_results = contextual_results
        else:
            # Fallback to standard extractor
            suggested_results = extractor.extract(prompt)

            if isinstance(suggested_results, dict) and "commands" in suggested_results:
                suggested_results = suggested_results["commands"]

            if not suggested_results:
                suggested_results = []
            elif isinstance(suggested_results, dict) and "commands" in suggested_results:
                suggested_results = suggested_results["commands"]
            elif not isinstance(suggested_results, list):
                suggested_results = []

        valid_results = [
            r for r in suggested_results
            if isinstance(r, dict) and "action" in r and ("object" in r or "device" in r)
        ]

        if valid_results:
            print("\nSmart Home Commands Detected:")
            for result in valid_results:
                print(f"Action: {result['action']}")
                print(f"Object: {result.get('object') or result.get('device')}")
                if 'room' in result:
                    print(f"Room: {result['room']}")
                print(f"Valid: {result.get('valid', True)}")
                print(f"Score: {result.get('score', 'N/A')}")

            save_tasks_to_csv(valid_results)

            if is_device_control_command(valid_results):
                for result in valid_results:
                    mqtt_data = {
                        "device": result.get("object") or result.get("device"),
                        "action": result["action"],
                        "room": result.get("room"),
                        "valid": result.get("valid", True),
                        "source": "llm_voice"
                    }

                    success = publish_to_shiftr(mqtt_data)

                    if success:
                        print("Successfully sent to shiftr:")
                        print(mqtt_data)
                    else:
                        print("Failed to send to shiftr:")
                        print(mqtt_data)

        print("\nCaregiver Response:")
        print(assistant_response)
        print("\n" + "=" * 50)

        return {
            "status": "success",
            "message": "Voice processed successfully",
            "text": prompt,
            "response": assistant_response,
            "smart_home": valid_results
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "text": "",
            "response": "",
            "smart_home": []
        }

def process_voice_command():
    """Main function to process voice commands"""
    print("=== Caregiver Started ===")
    print("Caregiver is preparing... (Press Ctrl+C to stop)")
    
    while True:
        try:
            result = process_one_voice_command()

            if result["status"] == "error":
                print(result["message"])

            time.sleep(1)

        except KeyboardInterrupt:
            print("\n👋 Voice Assistant stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

@app.route("/")
def home():
    return "Voice-enabled Smart Home Assistant is running."

# @app.route("/start_voice", methods=["POST"])
# def start_voice():
#     """API endpoint to start voice processing"""
#     threading.Thread(target=process_voice_command, daemon=True).start()
#     return {"status": "Voice assistant started"}

@app.route("/start_voice", methods=["POST"])
def start_voice():
    result = process_one_voice_command()

    if result["status"] == "error":
        return jsonify(result), 400

    return jsonify(result)

# if __name__ == "__main__":
#     # Initialize log file
#     if not os.path.exists(LOG_FILE):
#         with open(LOG_FILE, 'w', encoding='utf-8') as f:
#             f.write("Conversation Log:\n" + "=" * 50 + "\n")
    
#     # print("Choose mode:")
#     # print("1. Run Flask server (with /start_voice endpoint)")
#     # print("2. Run voice assistant directly")
    
#     # choice = input("Enter choice (1 or 2): ").strip()
    
#     # if choice == "1":
#     #     app.run(debug=True)
#     # elif choice == "2":
#         # Check if VOSK model path exists
#     if not os.path.exists(VOSK_MODEL_PATH):
#         print(f"Please update VOSK_MODEL_PATH to your actual Vosk model directory")
#         print(f"Current path: {VOSK_MODEL_PATH}")
#         VOSK_MODEL_PATH = input("Enter correct Vosk model path: ").strip()
    
#     process_voice_command()
#     # else:
#     #     print("Invalid choice. Exiting...")

if __name__ == "__main__":
    # Initialize log file
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("Conversation Log:\n" + "=" * 50 + "\n")

    # Check if VOSK model path exists
    if not os.path.exists(VOSK_MODEL_PATH):
        print("Please update VOSK_MODEL_PATH to your actual Vosk model directory")
        print(f"Current path: {VOSK_MODEL_PATH}")
        VOSK_MODEL_PATH = input("Enter correct Vosk model path: ").strip()

    app.run(debug=True, port=8000)
    