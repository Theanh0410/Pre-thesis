import os
import json
import requests
import pandas as pd
import time
import threading
from flask import Flask, jsonify, session, request
from flask_cors import CORS
from SmartHomeCommandExtractor import SmartHomeCommandExtractor
from ContextualCommandProcessor import ContextualCommandProcessor, correct_voice_mishearing
from intent_matching import IntentMatcher
from RAG.bm25 import BM25Retriever
from silence_detector import EndOfSpeechDetector
from health_advice import (
    BLOOD_PRESSURE_ADVICE,
    BLOOD_PRESSURE_EMERGENCY_ADVICE,
    classify_blood_pressure,
)

# Import speech to text functionality
import wave
import numpy as np
from vosk import Model, KaldiRecognizer
import sounddevice as sd
from sentence_transformers import SentenceTransformer

# Import ThingSpeak functionality
import logging

app = Flask(__name__)
CORS(app, origins="*", supports_credentials=True)
app.secret_key = 'your_secret_key'

# Configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

# The web dashboard (web/app.py) owns the resident's health profile
# (age/sex/BP/pulse/weight/height, edited from the profile page). This
# server has no login of its own, so it reads it over HTTP using the same
# shared internal key web/app.py checks - keep these two values in sync.
WEB_APP_URL = "http://localhost:5000"
INTERNAL_API_KEY = "smart-home-internal-9f3a1c"
LOG_FILE = 'conversation_log.txt'
TASK_FILE = os.path.join(os.path.dirname(__file__), "caregiver_command.csv")
VOSK_MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "vosk-model-en-us-0.22")
vosk_model = Model(VOSK_MODEL_PATH)

import paho.mqtt.client as mqtt
import json

MQTT_BROKER = "theanh0410.cloud.shiftr.io"
MQTT_PORT = 1883
MQTT_USERNAME = "theanh0410"
MQTT_PASSWORD = "eoCNam4gR2IWOA6d"
MQTT_TOPIC = "home/control"
MQTT_TOPIC_HEALTH_LOG = "home/health_log"

mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_client.loop_start()

def publish_to_shiftr(command_data):
    payload = json.dumps(command_data)
    result = mqtt_client.publish(MQTT_TOPIC, payload)
    return result.rc == 0

def publish_health_log(log_data):
    payload = json.dumps(log_data)
    result = mqtt_client.publish(MQTT_TOPIC_HEALTH_LOG, payload)
    return result.rc == 0

def fetch_health_profile():
    """Best-effort fetch of the resident's body measurements from the web
    dashboard. Returns None if the web server is unreachable or the request
    fails - the health RAG prompt just falls back to generic guidance."""
    try:
        response = requests.get(
            f"{WEB_APP_URL}/api/health_profile/default",
            headers={"X-Internal-Key": INTERNAL_API_KEY},
            timeout=3
        )
        if response.status_code == 200:
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch health profile: {e}")
    return None

def format_health_profile(profile):
    """Render the fetched profile as a short block for the prompt, skipping
    any fields the user hasn't filled in. Returns "" if nothing is set."""
    if not profile:
        return ""

    lines = []
    if profile.get("age") is not None:
        lines.append(f"Age: {profile['age']}")
    if profile.get("sex"):
        lines.append(f"Sex: {profile['sex']}")
    if profile.get("systolic") is not None and profile.get("diastolic") is not None:
        lines.append(f"Blood pressure: {profile['systolic']}/{profile['diastolic']} mmHg")
    if profile.get("pulse") is not None:
        lines.append(f"Pulse: {profile['pulse']} bpm")
    if profile.get("weight_kg") is not None:
        lines.append(f"Weight: {profile['weight_kg']} kg")
    if profile.get("height_cm") is not None:
        lines.append(f"Height: {profile['height_cm']} cm")

    return "\n".join(lines)


def handle_profile_lookup(prompt):
    """Answers "what are my measurements" style questions by reciting the
    stored profile directly, deterministically - no LLM involved, so there's
    no risk of it inventing or altering numbers it's just supposed to repeat."""
    profile = fetch_health_profile()
    formatted = format_health_profile(profile)

    if formatted:
        assistant_response = "Here are your stored body measurements:\n" + formatted
    else:
        assistant_response = (
            "You don't have any body measurements saved yet. You (or your "
            "caregiver) can add them from your profile page on the dashboard."
        )

    conversation_id = str(hash(f"{prompt}{assistant_response}"))
    write_to_txt(prompt, assistant_response, conversation_id)
    update_context(prompt, assistant_response, use_flask_session=False)

    save_health_log_to_csv(prompt, "profile_lookup", assistant_response, [])
    publish_health_log({
        "condition_tag": "profile_lookup",
        "question": prompt,
        "answer": assistant_response,
        "retrieved_docs": [],
        "source": "llm_voice",
        "bp_status": None,
        "bp_emergency": False
    })

    print("\nCaregiver Response:")
    print(assistant_response)
    print("\n" + "=" * 50)

    return {
        "status": "success",
        "message": "Voice processed successfully",
        "text": prompt,
        "response": assistant_response,
        "smart_home": [],
        "health_topic": "profile_lookup",
        "bp_status": None,
        "bp_emergency": False
    }

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
with open("smarthome/intents.json") as f:
    intents = json.load(f)
with open("smarthome/health_intents.json") as f:
    health_intents = json.load(f)

# Loaded once and shared between the extractor (direct commands) and the
# contextual processor (natural/indirect phrasing like "I want to go to
# bed") so the ~130MB model isn't loaded into memory twice.
embedding_model = SentenceTransformer("paraphrase-MiniLM-L12-v2")


def embed_texts(texts):
    return embedding_model.encode(texts, convert_to_tensor=False).tolist()


extractor = SmartHomeCommandExtractor(
    actions=actions,
    synonym_map=synonym_map,
    room_actions=room_actions,
    object_room_map=object_room_map,
    threshold=0.1,
    model=embedding_model
)

contextual_processor = ContextualCommandProcessor(
    intents=intents,
    embed_fn=embed_texts,
    room_actions=room_actions,
    object_room_map=object_room_map
)

bm25_retriever = BM25Retriever(docs_folder="documents")

# Health consultation feature: separate corpus + intent matcher so patient
# education material doesn't dilute BM25 relevance for smart-home documents.
health_bm25_retriever = BM25Retriever(docs_folder="documents/health")
health_matcher = IntentMatcher(health_intents, embed_fn=embed_texts)
HEALTH_LOG_FILE = os.path.join(os.path.dirname(__file__), "health_consultation_log.csv")

ROOM_ID_MAP = {
    "living room": 201,
    "kitchen": 1,
    "bedroom": 301,
    "bathroom": 401
}


def speech_to_text(timeout=10, sample_rate=16000, silence_duration=1.5,
                   silence_threshold=200, no_speech_timeout=5):
    """Record from the microphone until the speaker stops, then transcribe.

    Recording ends `silence_duration` seconds after speech was last heard
    (see silence_detector.EndOfSpeechDetector), or after `no_speech_timeout`
    seconds if nobody speaks, or after `timeout` seconds in total. Raise
    `silence_threshold` if background noise keeps it recording; lower it if
    it cuts off quiet speakers."""
    try:
        recognizer = KaldiRecognizer(vosk_model, sample_rate)
        detector = EndOfSpeechDetector(
            sample_rate=sample_rate,
            energy_threshold=silence_threshold,
            silence_duration=silence_duration,
            no_speech_timeout=no_speech_timeout,
            max_duration=timeout,
        )

        print("Please say something that I can help you...")

        # Read 100ms chunks and feed them to Vosk as they arrive, so the
        # transcript is nearly ready the moment the speaker stops.
        chunk_size = sample_rate // 10
        reason = None
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype='int16',
                            blocksize=chunk_size) as stream:
            while reason is None:
                chunk, _overflowed = stream.read(chunk_size)
                chunk = chunk.reshape(-1)
                recognizer.AcceptWaveform(chunk.tobytes())
                reason = detector.update(chunk)

        # Always ask Vosk, even after "no_speech": a quiet microphone can sit
        # below the energy threshold and still be understood by the recognizer.
        text = json.loads(recognizer.FinalResult()).get("text", "")
        print(f"Recording stopped ({reason}); loudest level {detector.peak_energy:.0f} "
              f"(speech threshold {silence_threshold}); heard: {text!r}")

        # Clean up memory
        del recognizer
        import gc
        gc.collect()

        return text

    except Exception as e:
        print(f"Error in speech_to_text: {e}")
        return ""


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

def save_health_log_to_csv(question, condition_tag, answer, retrieved_filenames, bp_result=None):
    if not os.path.exists(HEALTH_LOG_FILE) or os.stat(HEALTH_LOG_FILE).st_size == 0:
        df_existing = pd.DataFrame()
        current_id = 1
    else:
        df_existing = pd.read_csv(HEALTH_LOG_FILE)
        if "ID" not in df_existing.columns or df_existing["ID"].dropna().empty:
            current_id = 1
        else:
            current_id = int(df_existing["ID"].max()) + 1

    new_row = pd.DataFrame([{
        "ID": current_id,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "condition_tag": condition_tag,
        "question": question,
        "answer": answer,
        "retrieved_docs": ", ".join(retrieved_filenames),
        "bp_status": bp_result["status"] if bp_result else "",
        "bp_emergency": bp_result["is_emergency"] if bp_result else "",
    }])

    if df_existing.empty:
        new_row.to_csv(HEALTH_LOG_FILE, index=False)
    else:
        pd.concat([df_existing, new_row], ignore_index=True).to_csv(HEALTH_LOG_FILE, index=False)

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
    """Record and process one voice input and return result for web/API use"""
    try:
        prompt = speech_to_text()

        if not prompt.strip():
            return {
                "status": "error",
                "message": "No speech detected",
                "text": "",
                "response": "",
                "smart_home": []
            }

        print(f"\nVoice Input: {prompt}")
        return process_text_input(prompt)

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "text": "",
            "response": "",
            "smart_home": []
        }

def process_text_input(prompt):
    """Process a single utterance (typed or transcribed) through the same
    health-RAG / smart-home pipeline, and return result for web/API use."""
    try:
        # Process with AI
        context = get_context(use_flask_session=False)

        # Health consultation: route to the health corpus + a strict,
        # non-diagnostic prompt instead of the generic smart-home chat one.
        health_matches = health_matcher.match(correct_voice_mishearing(prompt), threshold=0.6)
        condition_tag = health_matches[0].actions[0]["condition"] if health_matches else None

        if condition_tag == "profile_lookup":
            return handle_profile_lookup(prompt)

        if condition_tag:
            health_docs = health_bm25_retriever.get_top_k_filenames(prompt, k=3)
            health_context = "\n\n".join(doc for _, doc in health_docs)
            retrieved_filenames = [filename for filename, _ in health_docs]

            health_profile = fetch_health_profile()
            patient_info = format_health_profile(health_profile)
            patient_info_block = f"\n        Patient Info:\n        {patient_info}\n" if patient_info else ""

            bp_result = None
            if condition_tag == "hypertension" and health_profile:
                bp_result = classify_blood_pressure(
                    health_profile.get("systolic"), health_profile.get("diastolic")
                )

            instructions = (
                "You are a health-information assistant for older adults.\n"
                "        Answer using ONLY the reference material below. Do not diagnose or\n"
                "        prescribe medication. Always encourage the user to consult their\n"
                "        doctor for anything personalized or urgent."
            )

            bp_status_block = ""
            if bp_result:
                status = bp_result["status"]
                advice = BLOOD_PRESSURE_EMERGENCY_ADVICE if bp_result["is_emergency"] else BLOOD_PRESSURE_ADVICE[status]
                emergency_note = " (POSSIBLE EMERGENCY)" if bp_result["is_emergency"] else ""
                bp_status_block = (
                    f"\n        Blood Pressure Status: {status}{emergency_note}\n"
                    f"        Suggested Advice: {advice}\n"
                )
                instructions += (
                    "\n        A Blood Pressure Status and Suggested Advice are given below, "
                    "already determined from the patient's actual reading - state the "
                    "status plainly and explain the advice in your own words. Do not "
                    "recalculate, second-guess, or contradict the given status."
                )
            elif patient_info:
                instructions += (
                    "\n        If patient info is provided below, you may say whether their "
                    "reported numbers fall inside or outside the ranges described in the "
                    "reference material."
                )

            combined_prompt = f"""

        {instructions}
        {patient_info_block}{bp_status_block}
        Reference Material:
        {health_context}

        User: {prompt}
        Assistant:"""
        else:
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

        if condition_tag:
            save_health_log_to_csv(prompt, condition_tag, assistant_response, retrieved_filenames, bp_result)
            publish_health_log({
                "condition_tag": condition_tag,
                "question": prompt,
                "answer": assistant_response,
                "retrieved_docs": retrieved_filenames,
                "source": "llm_voice",
                "bp_status": bp_result["status"] if bp_result else None,
                "bp_emergency": bp_result["is_emergency"] if bp_result else False
            })
            print("\nCaregiver Response:")
            print(assistant_response)
            print("\n" + "=" * 50)
            return {
                "status": "success",
                "message": "Voice processed successfully",
                "text": prompt,
                "response": assistant_response,
                "smart_home": [],
                "health_topic": condition_tag,
                "bp_status": bp_result["status"] if bp_result else None,
                "bp_emergency": bp_result["is_emergency"] if bp_result else False
            }

        # Extract smart home commands
        # Step 1: Try contextual processor first (comfort/emotional states)
        contextual_results = contextual_processor.process_contextual_command(prompt)
        contextual_valid_results = [r for r in contextual_results if r.get("valid")]

        if contextual_valid_results:
            # High confidence contextual match - use this
            suggested_results = contextual_valid_results
        else:
            # Fallback to standard extractor
            suggested_results = extractor.extract(prompt)

            if isinstance(suggested_results, dict) and "commands" in suggested_results:
                suggested_results = suggested_results["commands"]

            if not isinstance(suggested_results, list):
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
                        "valid": result.get("valid", False),
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
            "smart_home": valid_results,
            "health_topic": None
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
            print("\nVoice Assistant stopped by user")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

@app.route("/")
def home():
    return "Voice-enabled Smart Home Assistant is running."


@app.route("/start_voice", methods=["POST"])
def start_voice():
    result = process_one_voice_command()

    if result["status"] == "error":
        return jsonify(result), 400

    return jsonify(result)

@app.route("/process_text", methods=["POST"])
def process_text():
    """Same pipeline as /start_voice, but for typed input - useful when
    speech recognition misheard something."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()

    if not text:
        return jsonify({
            "status": "error",
            "message": "No text provided",
            "text": "",
            "response": "",
            "smart_home": []
        }), 400

    print(f"\nText Input: {text}")
    result = process_text_input(text)

    if result["status"] == "error":
        return jsonify(result), 400

    return jsonify(result)


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
    