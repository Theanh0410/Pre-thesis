from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import threading
import requests
import json
import os
import re
from flask_mysqldb import MySQL

# Import Blueprints from login.py and register.py
from login import login_bp
from register import register_bp

# --- MQTT Configuration ---
MQTT_BROKER = "theanh0410.cloud.shiftr.io"
MQTT_PORT = 1883
MQTT_USER = "theanh0410"  
MQTT_PASSWORD = "eoCNam4gR2IWOA6d"  
MQTT_TOPIC_CONTROL = "home/control"
MQTT_TOPIC_SENSORS = "home/sensors"
MQTT_TOPIC_HEALTH_LOG = "home/health_log"

# The LLM voice server has no login/session of its own, so a spoken health
# question can't be tagged with a specific web-dashboard user. This is a
# single-resident prototype, so consultations are attributed to one fixed
# account; a real multi-resident deployment would need the voice device to
# identify its user before this can be more than a placeholder.
# NOTE: must be an id that exists in `users` (FK constraint) - update this
# if you re-create your dev database or switch test accounts.
DEFAULT_RESIDENT_USER_ID = 14

# Shared secret so the LLM server (which has no login of its own) can pull
# the resident's health profile without this endpoint being open to anyone
# who can reach this dev server on the network (it binds to 0.0.0.0).
INTERNAL_API_KEY = "smart-home-internal-9f3a1c"

# --- Flask and SocketIO Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'smart_home_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'  # Or localhost
app.config['MYSQL_USER'] = 'root'  # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'bin04102004'  # Your MySQL password
app.config['MYSQL_DB'] = 'thesis'  # The database you created (thesis)

mysql = MySQL(app)

# --- Avatar upload configuration ---
AVATAR_UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(AVATAR_UPLOAD_FOLDER, exist_ok=True)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB, covers avatar uploads

def allowed_avatar_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS

# --- MQTT Client Setup ---
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

# --- Handle MQTT messages ---
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"MQTT Message Received: {msg.topic} -> {payload}")

    if msg.topic == MQTT_TOPIC_SENSORS:
        try:
            # Parse payload - handle both old format "humidity,light_level" and new format "room,humidity,light_level"
            parts = payload.split(',')
            
            if len(parts) == 3:  # New format: "room,humidity,light_level"
                room, humidity, light_level = parts
            elif len(parts) == 2:  # Old format: "humidity,light_level"
                humidity, light_level = parts
                room = "living room"  # Default room
            else:
                print(f"Error: Invalid sensor data format: {payload}")
                return
            
            # Emit sensor data with room information using socketio.server.emit for background thread
            socketio.server.emit('sensor_data', {
                'humidity': humidity, 
                'light_level': light_level,
                'room': room
            }, to=None)
            print(f"✓ Sensor data emitted: {room} | humidity={humidity}%, light={light_level}")
        except (ValueError, IndexError) as e:
            print(f"Error parsing sensor data: {e}")

    elif msg.topic == MQTT_TOPIC_CONTROL:
        try:
            data = json.loads(payload)

            if not data.get("valid", False):
                print("Ignoring invalid command")
                return

            ui_command = map_llm_command_to_ui(data)

            if ui_command:
                socketio.server.emit('device_status', {'command': ui_command}, to=None)
                print(f"Emitted device_status: {ui_command}")
            else:
                print(f"Could not map command: {data}")
        except json.JSONDecodeError:
            socketio.server.emit('device_status', {'command': payload}, to=None)

    elif msg.topic == MQTT_TOPIC_HEALTH_LOG:
        try:
            data = json.loads(payload)
            condition_tag = data.get("condition_tag")
            question = data.get("question", "")
            answer = data.get("answer", "")
            retrieved_docs = data.get("retrieved_docs")
            if isinstance(retrieved_docs, list):
                retrieved_docs = ", ".join(retrieved_docs)

            # flask_mysqldb's `mysql.connection` reads from flask.g, which
            # requires an active app context - this callback runs on the
            # background MQTT thread, outside any Flask request.
            with app.app_context():
                cursor = mysql.connection.cursor()
                cursor.execute(
                    """
                    INSERT INTO health_logs (user_id, condition_tag, question, answer, retrieved_docs)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (DEFAULT_RESIDENT_USER_ID, condition_tag, question, answer, retrieved_docs)
                )
                mysql.connection.commit()
                log_id = cursor.lastrowid
                cursor.close()

            socketio.server.emit('health_log', {
                'id': log_id,
                'condition_tag': condition_tag,
                'question': question,
                'answer': answer,
                'retrieved_docs': retrieved_docs,
            }, to=None)
            print(f"Health log stored & emitted: {condition_tag}")
        except Exception as e:
            print(f"Error handling health log message: {e}")

# --- MQTT connection setup ---
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_SENSORS)
    client.subscribe(MQTT_TOPIC_CONTROL)
    client.subscribe(MQTT_TOPIC_HEALTH_LOG)

client.on_connect = on_connect
client.on_message = on_message

# --- Start MQTT in Background ---
def mqtt_thread_func():
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT connection error: {e}")

# --- Device Control Functions ---
def send_mqtt_command(command):
    print(f"Sending command to ESP32: {command}")
    client.publish(MQTT_TOPIC_CONTROL, command)

def map_llm_command_to_ui(data):
    device = (data.get("device") or "").lower()
    action = (data.get("action") or "").lower()
    room = (data.get("room") or "").lower()

    room_device_map = {
        ("living room", "light"): "livingroom_light",
        ("bedroom", "light"): "bedroom_light",
        ("living room", "fan"): "livingroom_fan",
        ("bedroom", "fan"): "bedroom_fan",
    }

    base = room_device_map.get((room, device))
    if not base:
        return None

    if action in ["turn on", "open", "switch on"]:
        return f"{base}_on"
    if action in ["turn off", "close", "switch off"]:
        return f"{base}_off"

    return None

# --- Routes for Flask ---

# Register the Blueprints
app.register_blueprint(login_bp)
app.register_blueprint(register_bp)

def seed_default_rooms(user_id):
    """Give a new account the same starter rooms/devices the old hardcoded
    dashboard always displayed (Living Room + Bedroom, each with a light and
    a fan), so accounts start populated instead of with an empty grid."""
    cursor = mysql.connection.cursor()
    for room_name in ("Living Room", "Bedroom"):
        cursor.execute(
            "INSERT INTO rooms (user_id, room_name) VALUES (%s, %s)",
            (user_id, room_name)
        )
        room_id = cursor.lastrowid
        for device_type_id, custom_name in ((1, f"{room_name} Light"), (2, f"{room_name} Fan")):
            cursor.execute(
                "INSERT INTO devices (room_id, device_type_id, custom_name, status) VALUES (%s, %s, %s, 'off')",
                (room_id, device_type_id, custom_name)
            )
    mysql.connection.commit()
    cursor.close()

def normalize_room_code(room_name):
    """Matches the JS normalizeRoomName() in index.html - must stay in sync."""
    return re.sub(r'[^a-z0-9]', '', (room_name or '').lower())

ROOM_ICON_KEYWORDS = {
    'bed': 'bed',
    'bath': 'bath',
    'kitchen': 'kitchen-set',
    'living': 'couch',
    'garage': 'warehouse',
    'office': 'briefcase',
}

def room_icon(room_name):
    name = (room_name or '').lower()
    for keyword, icon in ROOM_ICON_KEYWORDS.items():
        if keyword in name:
            return icon
    return 'house-chimney'

def get_rooms_with_devices(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, room_name FROM rooms WHERE user_id = %s ORDER BY id", (user_id,))
    rooms = cursor.fetchall()

    room_list = []
    for room_id, room_name in rooms:
        room_code = normalize_room_code(room_name)
        cursor.execute(
            """
            SELECT d.id, d.custom_name, d.status, dt.device_code
            FROM devices d
            JOIN device_types dt ON dt.id = d.device_type_id
            WHERE d.room_id = %s
            ORDER BY d.id
            """,
            (room_id,)
        )
        devices = [
            {
                'id': row[0],
                'custom_name': row[1],
                'status': row[2],
                'device_code': row[3],
                'command_base': f"{room_code}_{row[3]}",
                'icon': 'fan' if row[3] == 'fan' else 'lightbulb',
            }
            for row in cursor.fetchall()
        ]
        room_list.append({'id': room_id, 'name': room_name, 'icon': room_icon(room_name), 'devices': devices})

    cursor.close()
    return room_list

@app.route('/')
def home():
    # Redirect to login if user is not logged in
    if 'username' not in session:
        return redirect(url_for('login.login'))
    rooms = get_rooms_with_devices(session['user_id'])
    return render_template('index.html', rooms=rooms)

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login.login'))  # Redirect to login page

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login.login'))
    rooms = get_rooms_with_devices(session['user_id'])
    return render_template('index.html', rooms=rooms)

@app.route('/control', methods=['POST'])
def control_device():
    data = request.json
    command = data.get('command')

    if command:
        send_mqtt_command(command)
        return jsonify({"status": "success", "message": f"Command '{command}' sent."})
    
    return jsonify({"status": "error", "message": "Invalid command."}), 400


@app.route('/add_room', methods=['POST'])
def add_room():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 400
    
    user_id = session['user_id']
    room_name = request.json.get('room_name')
    
    # Insert new room into the database
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO rooms (user_id, room_name) VALUES (%s, %s)", (user_id, room_name))
    mysql.connection.commit()
    
    # Get the newly added room's id and device types
    cursor.execute("SELECT id FROM rooms WHERE room_name = %s AND user_id = %s", (room_name, user_id))
    room_id = cursor.fetchone()[0]
    
    cursor.execute("SELECT * FROM devices WHERE room_id = %s", (room_id,))
    devices = cursor.fetchall()

    cursor.close()

    return jsonify({
        "status": "success",
        "message": "Room added successfully",
        "room_id": room_id,
        "room_name": room_name,
        "devices": devices
    })

@app.route('/remove_room', methods=['POST'])
def remove_room():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 400
    
    room_id = request.json.get('room_id')

    # Remove room
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM rooms WHERE id = %s", (room_id,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"status": "success", "message": "Room removed successfully"})

@app.route('/add_device', methods=['POST'])
def add_device():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 400

    room_id = request.json.get('room_id')
    device_type_id = request.json.get('device_type_id')
    custom_name = request.json.get('custom_name')

    if not room_id or not device_type_id or not custom_name:
        return jsonify({
            "status": "error",
            "message": "Missing room, device type, or device name."
        }), 400
    
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO devices (room_id, device_type_id, custom_name, status)
        VALUES (%s, %s, %s, 'off')
        """,
        (room_id, device_type_id, custom_name)
    )

    mysql.connection.commit()

    device_id = cursor.lastrowid

    cursor.close()
    
    return jsonify({
        "status": "success",
        "message": "Device added successfully",
        "device_id": device_id
    })

@app.route('/remove_device', methods=['POST'])
def remove_device():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 400
    
    device_id = request.json.get('device_id')

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM devices WHERE id = %s", (device_id,))
    mysql.connection.commit()
    cursor.close()

    return jsonify({"status": "success", "message": "Device removed successfully"})



@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login.login'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT u.fullname, u.username, u.email, u.created_at, u.avatar_path,
               hp.age, hp.sex, hp.systolic, hp.diastolic, hp.pulse, hp.weight_kg, hp.height_cm
        FROM users u
        LEFT JOIN health_profiles hp ON hp.user_id = u.id
        WHERE u.id = %s
        """,
        (session['user_id'],)
    )
    user = cursor.fetchone()
    cursor.close()

    return render_template('profile.html', user=user)

@app.route('/profile/avatar', methods=['POST'])
def update_avatar():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    file = request.files.get('avatar')
    if not file or file.filename == '':
        return jsonify({"status": "error", "message": "No file selected"}), 400

    if not allowed_avatar_file(file.filename):
        return jsonify({"status": "error", "message": "Unsupported file type"}), 400

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"user_{session['user_id']}.{ext}"
    file.save(os.path.join(AVATAR_UPLOAD_FOLDER, filename))

    avatar_path = f"uploads/avatars/{filename}"

    cursor = mysql.connection.cursor()
    cursor.execute("UPDATE users SET avatar_path = %s WHERE id = %s", (avatar_path, session['user_id']))
    mysql.connection.commit()
    cursor.close()

    session['avatar_path'] = avatar_path

    return jsonify({"status": "success", "avatar_url": url_for('static', filename=avatar_path)})

@app.route('/profile/health', methods=['POST'])
def update_health_profile():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    data = request.json or {}

    def to_int(value, min_value, max_value):
        try:
            n = int(value)
        except (TypeError, ValueError):
            return None, False
        if not (min_value <= n <= max_value):
            return None, False
        return n, True

    def to_float(value, min_value, max_value):
        try:
            n = float(value)
        except (TypeError, ValueError):
            return None, False
        if not (min_value <= n <= max_value):
            return None, False
        return n, True

    fields = {}
    errors = []

    if data.get('age') not in (None, ''):
        value, ok = to_int(data.get('age'), 0, 130)
        if not ok:
            errors.append("Age must be a number between 0 and 130.")
        fields['age'] = value

    sex = data.get('sex') or None
    if sex not in (None, '', 'male', 'female', 'other'):
        errors.append("Sex must be male, female, or other.")
    else:
        fields['sex'] = sex or None

    if data.get('systolic') not in (None, ''):
        value, ok = to_int(data.get('systolic'), 50, 300)
        if not ok:
            errors.append("Systolic pressure must be a number between 50 and 300 mmHg.")
        fields['systolic'] = value

    if data.get('diastolic') not in (None, ''):
        value, ok = to_int(data.get('diastolic'), 30, 200)
        if not ok:
            errors.append("Diastolic pressure must be a number between 30 and 200 mmHg.")
        fields['diastolic'] = value

    if data.get('pulse') not in (None, ''):
        value, ok = to_int(data.get('pulse'), 20, 250)
        if not ok:
            errors.append("Pulse must be a number between 20 and 250 bpm.")
        fields['pulse'] = value

    if data.get('weight_kg') not in (None, ''):
        value, ok = to_float(data.get('weight_kg'), 1, 400)
        if not ok:
            errors.append("Weight must be a number between 1 and 400 kg.")
        fields['weight_kg'] = value

    if data.get('height_cm') not in (None, ''):
        value, ok = to_float(data.get('height_cm'), 30, 250)
        if not ok:
            errors.append("Height must be a number between 30 and 250 cm.")
        fields['height_cm'] = value

    if errors:
        return jsonify({"status": "error", "message": " ".join(errors)}), 400

    columns = ["age", "sex", "systolic", "diastolic", "pulse", "weight_kg", "height_cm"]
    for column in columns:
        fields.setdefault(column, None)

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        INSERT INTO health_profiles (user_id, age, sex, systolic, diastolic, pulse, weight_kg, height_cm)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          age = VALUES(age),
          sex = VALUES(sex),
          systolic = VALUES(systolic),
          diastolic = VALUES(diastolic),
          pulse = VALUES(pulse),
          weight_kg = VALUES(weight_kg),
          height_cm = VALUES(height_cm)
        """,
        (
            session['user_id'], fields['age'], fields['sex'], fields['systolic'],
            fields['diastolic'], fields['pulse'], fields['weight_kg'], fields['height_cm']
        )
    )
    mysql.connection.commit()
    cursor.close()

    return jsonify({"status": "success"})

@app.route('/api/health_profile/default')
def api_default_health_profile():
    """Internal endpoint for the LLM server to read the resident's body
    measurements when answering health questions. Not for browser use -
    requires the shared internal API key, since this server binds to
    0.0.0.0 and has no session cookie to check for a server-to-server call."""
    if request.headers.get('X-Internal-Key') != INTERNAL_API_KEY:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    cursor = mysql.connection.cursor()
    cursor.execute(
        "SELECT age, sex, systolic, diastolic, pulse, weight_kg, height_cm "
        "FROM health_profiles WHERE user_id = %s",
        (DEFAULT_RESIDENT_USER_ID,)
    )
    row = cursor.fetchone()
    cursor.close()

    if not row:
        return jsonify({
            "age": None, "sex": None, "systolic": None, "diastolic": None,
            "pulse": None, "weight_kg": None, "height_cm": None
        })

    age, sex, systolic, diastolic, pulse, weight_kg, height_cm = row
    return jsonify({
        "age": age,
        "sex": sex,
        "systolic": systolic,
        "diastolic": diastolic,
        "pulse": pulse,
        "weight_kg": float(weight_kg) if weight_kg is not None else None,
        "height_cm": float(height_cm) if height_cm is not None else None,
    })

@app.route('/health')
def health_log():
    if 'username' not in session:
        return redirect(url_for('login.login'))

    cursor = mysql.connection.cursor()
    cursor.execute(
        """
        SELECT id, condition_tag, question, answer, retrieved_docs, created_at
        FROM health_logs
        ORDER BY created_at DESC
        LIMIT 50
        """
    )
    logs = cursor.fetchall()
    cursor.close()

    return render_template('health_log.html', logs=logs)

@app.route('/start_voice', methods=['POST'])
def start_voice():
    try:
        response = requests.post("http://localhost:8000/start_voice", timeout=60)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Cannot connect to LLM server: {str(e)}"
        }), 500

@app.route('/process_text', methods=['POST'])
def process_text():
    text = (request.json or {}).get('text', '').strip()
    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400

    try:
        response = requests.post("http://localhost:8000/process_text", json={"text": text}, timeout=60)
        data = response.json()
        return jsonify(data), response.status_code
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Cannot connect to LLM server: {str(e)}"
        }), 500

if __name__ == '__main__':
    # Start MQTT thread and Flask app
    mqtt_thread = threading.Thread(target=mqtt_thread_func, daemon=True)
    mqtt_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)