# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A voice-controlled smart home system (thesis project) with five independently-run components that
communicate over a shared MQTT broker rather than direct API calls to each other:

- **`LLM/server/`** — Python/Flask voice assistant backend. Does speech-to-text, NLU/command
  extraction, RAG-augmented chat via a local Ollama model, and publishes device commands to MQTT.
- **`LLM/client/`** — Next.js (pages router) frontend, mostly unmodified `create-next-app`
  scaffolding; not the primary UI.
- **`web/`** — Python/Flask + Flask-SocketIO dashboard with MySQL-backed auth/rooms/devices. Bridges
  MQTT (device commands + sensor data) to a browser UI in real time.
- **`mobile/SmartHomeMobileApp/`** — Expo/React Native app (`App.js`) that talks to the broker
  directly via `mqtt`/`socket.io-client`.
- **`arduino/arduino/arduino.ino`** — ESP8266 firmware (DHT11 + light sensor + light/fan relays)
  that subscribes/publishes to the same MQTT broker.

All five pieces are separate runtimes; there is no shared package manager or monorepo tooling. Work
inside the relevant subfolder for commands.

## Architecture / data flow

Everything is coordinated through **one public MQTT broker** (`theanh0410.cloud.shiftr.io`, hardcoded
in `LLM/server/app.py`, `web/app.py`, and `arduino/arduino/arduino.ino`), on two topics:

- `home/control` — device commands, JSON payloads like `{"device": "fan", "action": "turn on", "room": "living room", "valid": true, "source": "..."}`
- `home/sensors` — CSV payloads `"room,humidity,light_level"` (or legacy 2-field `"humidity,light_level"`, defaulted to living room) published by the Arduino

Flow: **voice/text input → `LLM/server` → MQTT `home/control`** ⇄ **`web/app.py` (subscribes,
re-emits over SocketIO to the dashboard; also republishes commands the dashboard UI issues)** ⇄
**Arduino firmware (subscribes `home/control`, publishes `home/sensors`)**. The mobile app connects to
the broker/SocketIO independently.

### `LLM/server` command pipeline (`app.py`)

For each voice/text utterance:
1. `speech_to_text()` (Vosk) transcribes audio, or text comes in directly via `/start_voice`.
2. The prompt + BM25-retrieved doc context (`RAG/bm25.py` over `documents/`) + conversation context is
   sent to a local Ollama server (`OLLAMA_URL`, model `llama3.2`) for a natural-language reply.
3. In parallel, command extraction runs two ways and picks whichever succeeds:
   - `ContextualCommandProcessor` first — matches indirect/natural phrasing ("I'm hot", "I want to go
     to bed") to one or more device actions via `IntentMatcher` (`intent_matching.py`): each intent in
     `smarthome/intents.json` carries example phrases + a list of `{device, action, room}` actions;
     the utterance is embedded (shared `SentenceTransformer`, see below) and matched by cosine
     similarity against every intent's examples, so new phrasings generalize without new code — add
     examples to the config instead. `ROOM_KEYWORDS`/`VOICE_MISHEARING_MAP` in
     `ContextualCommandProcessor.py` still handle explicit room overrides and Vosk mishearing
     correction as pre/post-processing around the match.
   - Falls back to `SmartHomeCommandExtractor` — sentence-embedding similarity (same shared
     `SentenceTransformer` model, passed in via its `model=` param so it isn't loaded twice) against
     `smarthome/actions.json`, with spaCy dependency parsing to pull the target object and
     `smarthome/synonyms.json` / `smarthome/room_actions.json` / `smarthome/object_room_map.json` to
     resolve synonyms, room, and validity.
4. Extracted commands are appended to `caregiver_command.csv` (`save_tasks_to_csv`, room name mapped
   to a numeric ID via `ROOM_ID_MAP`) and, if they look like device control, published to MQTT
   (`publish_to_shiftr`).
5. The full exchange is appended to `conversation_log.txt` and kept in a context buffer (Flask
   session when in a request context, a module-level `VOICE_CONTEXT` global otherwise — needed
   because the voice loop runs outside a request).

`smarthome/*.json` is the single source of truth for valid actions/rooms/objects/synonyms/intents
consumed by both the contextual processor and the extractor — update these together when adding a new
room or device type, matching the "add new room"/"add new device" work in recent commits. To teach the
contextual processor a new indirect phrase/intent (e.g. "I'm leaving the house"), add an entry to
`smarthome/intents.json` (example phrases + target actions) — no code change needed unless the new
intent needs logic beyond "match phrase → emit action(s)".

### `web/app.py`

Flask-SocketIO app with MySQL (`flask_mysqldb`) for users/rooms/devices, `login`/`register` Blueprints
in `login.py`/`register.py`. `map_llm_command_to_ui()` translates the LLM's `{device, room, action}`
JSON into the dashboard's internal command strings (e.g. `livingroom_light_on`); extend
`room_device_map` there when adding rooms/devices. There is no `requirements.txt` for this component —
dependencies (flask, flask-socketio, flask-mysqldb, paho-mqtt, bcrypt) must be installed manually into
its `venv`.

## Commands

### `LLM/server` (voice assistant backend)
```bash
conda activate llm                 # Python 3.10.x required (spaCy compatibility)
cd LLM/server
pip install -r requirements.txt
python -m spacy download en_core_web_sm
python -c "import nltk; nltk.download('punkt')"
python app.py                      # serves on port 8000, debug=True
```
Requires a local Ollama server running the `llama3.2` model (`ollama serve`) and a Vosk model at
`LLM/server/models/vosk-model-en-us-0.22/` (path is checked/prompted for at startup).

`test_intent_matching.py`, `test_contextual_command_processor.py`, and `test_smarthome_intents_config.py`
are real automated `unittest` suites (`python -m unittest discover -p "test_*.py"`) — they use a fake,
injected `embed_fn` instead of the real model, so they run without the heavy ML deps installed.
`test_contextual.py` and `test.py` are standalone manual scripts requiring the real
`sentence-transformers`/spaCy stack (run in the `llm` conda env, not a plain venv), used for
eyeballing real-model behavior rather than as pass/fail checks. `mock_sensor_publisher.py` /
`mock_sensor_publisher_advanced.py` publish fake `home/sensors` data to the MQTT broker for exercising
`web/app.py` without real hardware.

### `web/` (dashboard)
```bash
cd web
# activate/create venv, then: pip install flask flask-socketio flask-mysqldb paho-mqtt bcrypt requests
python app.py
```
Needs a local MySQL database named `thesis` (see `MYSQL_*` config in `app.py`) with `rooms`/`devices`
tables matching the queries in `app.py`/`login.py`/`register.py`.

### `LLM/client/` (Next.js, secondary UI)
```bash
cd LLM/client
npm run dev     # dev server, http://localhost:3000
npm run build
npm run lint
```

### `mobile/SmartHomeMobileApp/` (Expo app)
```bash
cd mobile/SmartHomeMobileApp
npm start        # expo start
npm run android
npm run ios
```

### `arduino/arduino/arduino.ino`
Flash via Arduino IDE/CLI to an ESP8266 (NodeMCU pinout). Requires `ESP8266WiFi`, `PubSubClient`,
`DHT`, and `ArduinoJson` libraries. WiFi SSID/password and MQTT credentials are hardcoded at the top of
the file and must be edited per deployment.

## Notes for making changes

- MQTT broker credentials and the MySQL password are hardcoded directly in `LLM/server/app.py`,
  `web/app.py`, and `arduino/arduino/arduino.ino` (same broker across all three) — when changing one,
  check whether the other two need the same update.
- `LLM/server/smarthome/*.json`, `web/app.py`'s `room_device_map`, and `ROOM_ID_MAP` in
  `LLM/server/app.py` each independently encode the set of valid rooms/devices; a new room or device
  generally needs updates in all three places, not just one.
- `LLM/.history/` is an editor auto-save trail (VS Code Local History), not meaningful project history
  — ignore it when searching for current implementations.
