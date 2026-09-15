from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import threading
import requests
import json
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

# --- MQTT connection setup ---
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(MQTT_TOPIC_SENSORS)
    client.subscribe(MQTT_TOPIC_CONTROL)

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

@app.route('/')
def home():
    # Redirect to login if user is not logged in
    if 'username' not in session:
        return redirect(url_for('login.login'))
    return render_template('index.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login.login'))  # Redirect to login page

@app.route('/dashboard')
def dashboard():
    return render_template('index.html')  # Display dashboard

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

if __name__ == '__main__':
    # Start MQTT thread and Flask app
    mqtt_thread = threading.Thread(target=mqtt_thread_func, daemon=True)
    mqtt_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)