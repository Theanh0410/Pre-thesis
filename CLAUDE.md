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
in `LLM/server/app.py`, `web/app.py`, and `arduino/arduino/arduino.ino`), on three topics:

- `home/control` — device commands, JSON payloads like `{"device": "fan", "action": "turn on", "room": "living room", "valid": true, "source": "..."}`
- `home/sensors` — CSV payloads `"room,humidity,light_level"` (or legacy 2-field `"humidity,light_level"`, defaulted to living room) published by the Arduino
- `home/health_log` — JSON `{condition_tag, question, answer, retrieved_docs, source, bp_status, bp_emergency}` published by `LLM/server` after every health consultation; `web/app.py` stores it in the `health_logs` table and re-emits it over SocketIO as `health_log`

`LLM/server` and `web/` also talk over plain HTTP: `web/app.py` proxies `/start_voice` and
`/process_text` to `LLM/server` (port 8000), and `LLM/server` reads the resident's body measurements
from `web/app.py` at `GET /api/health_profile/default` (header `X-Internal-Key`; the key is hardcoded
as `INTERNAL_API_KEY` in both files and must match).

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

### Health consultation pipeline (`LLM/server/app.py`, `process_text_input`)

Runs *before* the smart-home steps above; a matched health question never reaches command extraction.

1. `health_matcher` (`IntentMatcher` over `smarthome/health_intents.json`, threshold 0.6) tags the
   utterance with a `condition`: `diabetes`, `hypertension`, `arthritis`, or `profile_lookup`. Add a
   condition by adding an entry there plus a `documents/health/<condition>.txt` reference file.
2. `profile_lookup` is answered by `handle_profile_lookup` straight from the stored profile — no LLM, so
   numbers can't be altered.
3. Other conditions retrieve the top 3 docs from `documents/health/` (a separate `BM25Retriever`, kept
   apart from `documents/` so patient material doesn't dilute smart-home retrieval), fetch the profile
   from `web/` (`fetch_health_profile`, best-effort — falls back to generic guidance if `web/` is down),
   and prompt Ollama with a strict non-diagnostic instruction.
4. For `hypertension`, `classify_blood_pressure()` (in `health_advice.py`) computes Low/Normal/High plus
   an emergency flag in plain code; the result and canned advice are injected into the prompt and the
   model is told not to recompute it. Keep threshold logic in code, not in the prompt.
5. Each exchange is appended to `health_consultation_log.csv` and published to `home/health_log`.

`web/` side: `/profile` (avatar + age/sex/BP/pulse/weight/height, stored in `health_profiles`) and
`/health` (last 50 `health_logs`). Both tables are in `schema.sql`; an existing database needs
`migrations/001_add_avatar_and_health_profile.sql` (and `health_logs` if it predates it). Because the
voice server has no login, all consultations/profile reads are attributed to a single hardcoded
`DEFAULT_RESIDENT_USER_ID` in `web/app.py` — it must be an existing `users.id` (FK).

### `web/app.py`

Flask-SocketIO app with MySQL (`flask_mysqldb`) for users/rooms/devices, `login`/`register` Blueprints
in `login.py`/`register.py`. `map_llm_command_to_ui()` translates the LLM's `{device, room, action}`
JSON into the dashboard's internal command strings (e.g. `livingroom_light_on`); extend
`room_device_map` there when adding rooms/devices. There is no `requirements.txt` for this component —
dependencies (flask, flask-socketio, flask-mysqldb, paho-mqtt, bcrypt) must be installed manually into
its `venv`.

### Fine-tuning experiment (`LLM/finetune/`)

Thesis experiment, separate from the running system: QLoRA-fine-tune several small models for blood-pressure advice and
compare them. Nothing in `LLM/server` imports from here (the reverse is true: it reuses `LLM/server/health_advice.py`).

- `make_bp_dataset.py` generates `data/bp/{train,val,test}.jsonl` (+ `*_meta.jsonl` ground-truth sidecars). Labels come
  from `classify_blood_pressure`; splits are by *reading* (and topic), never per example, so a reading can't leak into test.
  Output is deterministic for a given `--seed`. If you change a threshold in `health_advice.py`, regenerate the data.
- `bp_finetune.ipynb` is the single Colab notebook (Unsloth) for every model/dataset; only its *Run config* cell changes
  (`RUN_NAME` picks a preset). It merges MedQuAD (only ~38 usable blood-pressure rows) with the generated files. Built from
  Unsloth's Llama 3.2 Conversational notebook; non-Llama presets are untested.
- `evaluate_ollama.py` scores any Ollama model on `dataset/test_BPquestions100.csv` (BPQA100, evaluation only - never train
  on it) and on the generated test set; `bp_eval.py` holds the pure scoring code, `make_table.py` builds the comparison table
  from `results/*.json`. Metrics: BPQA100 accuracy / precision / recall / F1 (Yes class) / macro-F1, BP-status per-class F1,
  emergency recall, doctor-referral rate. Always report macro-F1 and accuracy next to F1(Yes): a model that always says "Yes"
  gets F1(Yes) = 0.667 on the balanced BPQA100.
- BPQA100 is gated on Hugging Face and not git-ignored; check the repo's visibility before committing it. Its CSV column
  names are misleading: `replaced_question` is the question *with* the reading plus a label like "(high)"; `without_bp` is
  the redacted "s/d" version.
- `LLM/server/documents/health/hypertension.txt` says to discuss readings "at or above 140/90", while
  `classify_blood_pressure` labels 130/80+ as High. The generated data follows the classifier.

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

`test_intent_matching.py`, `test_contextual_command_processor.py`, `test_smarthome_intents_config.py`,
`test_health_advice.py`, and `test_silence_detector.py` are real automated `unittest` suites — they use a
fake, injected `embed_fn` instead of the real model, so they run without the heavy ML deps installed.
Run them by name:
`python -m unittest test_silence_detector test_health_advice test_intent_matching test_contextual_command_processor test_smarthome_intents_config`.
Plain `unittest discover` also collects `test_contextual.py`, which fails to import without the ML stack.
`app.py` itself can't be imported in tests (it loads Vosk and the embedding model at import time), so
logic that needs unit tests belongs in a separate module, as `health_advice.py` does.
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

### `LLM/finetune/` (fine-tuning experiment)
```bash
cd LLM/finetune
python make_bp_dataset.py                                   # regenerate data/bp/*.jsonl
python -m unittest test_make_bp_dataset test_bp_eval        # stdlib only; no GPU, Ollama or ML packages needed
python evaluate_ollama.py --model llama3.2 --tag llama32_3b-base --format-hint   # needs `ollama serve`
python make_table.py                                        # thesis comparison table from results/*.json
```
Training itself happens in Google Colab (T4) with `bp_finetune.ipynb`; see the notebook's header cell.

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
  check whether the other two need the same update. `INTERNAL_API_KEY` is duplicated in
  `LLM/server/app.py` and `web/app.py` the same way.
- `__pycache__/` and `*.pyc` are gitignored; don't re-add them.
- `LLM/server/server/smarthome/test_*.json` are fixtures that `test.py` generates — not a stray copy of
  `LLM/server/smarthome/`, and not read by `app.py`.
- `LLM/server/smarthome/*.json`, `web/app.py`'s `room_device_map`, and `ROOM_ID_MAP` in
  `LLM/server/app.py` each independently encode the set of valid rooms/devices; a new room or device
  generally needs updates in all three places, not just one.
- `LLM/.history/` is an editor auto-save trail (VS Code Local History), not meaningful project history
  — ignore it when searching for current implementations.
