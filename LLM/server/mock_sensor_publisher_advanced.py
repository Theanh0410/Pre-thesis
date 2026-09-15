"""
Advanced Mock Sensor Publisher with Multi-Room Support
Publishes mock data with room and device metadata
"""

import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime
from enum import Enum

# MQTT Configuration
MQTT_BROKER = "theanh0410.cloud.shiftr.io"
MQTT_PORT = 1883
MQTT_USER = "theanh0410"
MQTT_PASSWORD = "eoCNam4gR2IWOA6d"
MQTT_TOPIC_SENSORS = "home/sensors"

class Room(Enum):
    LIVING_ROOM = "living room"
    BEDROOM = "bedroom"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"

class AdvancedMockSensorPublisher:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.is_connected = False
        
        # Maintain state for realistic sensor variations
        self.room_states = {
            Room.LIVING_ROOM: {"humidity": 50, "light": 600},
            Room.BEDROOM: {"humidity": 55, "light": 400},
            Room.KITCHEN: {"humidity": 65, "light": 800},
            Room.BATHROOM: {"humidity": 75, "light": 300},
        }
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✓ Connected to MQTT Broker: {MQTT_BROKER}")
            self.is_connected = True
        else:
            print(f"✗ Failed to connect, return code {rc}")
            self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            print(f"✗ Unexpected disconnection. Return code: {rc}")
        self.is_connected = False
    
    def connect(self):
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            time.sleep(1)
            return self.is_connected
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def generate_sensor_data(self, room):
        """Generate realistic sensor data with gradual variations"""
        current_state = self.room_states[room]
        
        # Add small random fluctuations for realistic variation
        humidity_variation = random.uniform(-1, 1)
        light_variation = random.uniform(-15, 15)
        
        humidity = max(20, min(95, current_state["humidity"] + humidity_variation))
        light = max(50, min(1023, current_state["light"] + light_variation))
        
        # Update state
        self.room_states[room]["humidity"] = humidity
        self.room_states[room]["light"] = light
        
        return round(humidity, 1), int(light)
    
    def publish_sensor_data(self, room=None):
        """Publish mock sensor data for a specific room or all rooms"""
        if not self.is_connected:
            print("✗ Not connected to MQTT broker")
            return False
        
        rooms = [room] if room else Room
        all_published = True
        
        for r in rooms:
            humidity, light = self.generate_sensor_data(r)
            
            # Format: "room,humidity,light_level" for consistency
            payload = f"{r.value},{humidity},{light}"
            
            try:
                result = self.client.publish(MQTT_TOPIC_SENSORS, payload)
                
                if result.rc == 0:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] ✓ {r.value:15} | Humidity: {humidity:5.1f}% | Light: {light:4d}")
                else:
                    print(f"✗ Failed to publish for {r.value}")
                    all_published = False
            except Exception as e:
                print(f"✗ Publish error for {r.value}: {e}")
                all_published = False
        
        return all_published
    
    def publish_json_metadata(self, room):
        """Optional: Publish extended sensor data as JSON"""
        humidity, light = self.generate_sensor_data(room)
        
        data = {
            "room": room.value,
            "humidity": humidity,
            "light_level": light,
            "temperature": round(random.uniform(20, 28), 1),
            "co2": random.randint(300, 800),
            "timestamp": datetime.now().isoformat()
        }
        
        payload = json.dumps(data)
        
        try:
            result = self.client.publish(MQTT_TOPIC_SENSORS, payload)
            return result.rc == 0
        except Exception as e:
            print(f"✗ Error publishing JSON: {e}")
            return False
    
    def start_publishing_all_rooms(self, interval=5):
        """Publish data from all rooms simultaneously"""
        print(f"\n🌐 Advanced Mock Sensor Publisher Started")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Topic: {MQTT_TOPIC_SENSORS}")
        print(f"   Interval: {interval} seconds")
        print(f"   Rooms: {', '.join([r.value for r in Room])}")
        print("\nPublishing mock sensor data (Press Ctrl+C to stop)...\n")
        
        try:
            while True:
                self.publish_sensor_data()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\n👋 Mock Sensor Publisher stopped by user")
        finally:
            self.stop()
    
    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("✓ Disconnected from MQTT broker")


def main():
    publisher = AdvancedMockSensorPublisher()
    
    if publisher.connect():
        publisher.start_publishing_all_rooms(interval=5)
    else:
        print("✗ Failed to establish MQTT connection")


if __name__ == "__main__":
    main()
