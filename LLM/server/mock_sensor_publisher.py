"""
Mock Sensor Data Publisher for Smart Home MQTT System
Publishes simulated humidity and light level data to the MQTT broker
"""

import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime

# MQTT Configuration (same as in app.py)
MQTT_BROKER = "theanh0410.cloud.shiftr.io"
MQTT_PORT = 1883
MQTT_USER = "theanh0410"
MQTT_PASSWORD = "eoCNam4gR2IWOA6d"
MQTT_TOPIC_SENSORS = "home/sensors"

# Sensor configuration
SENSOR_UPDATE_INTERVAL = 5  # seconds between updates

class MockSensorPublisher:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self.client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.is_connected = False
        
        # Maintain state for smooth sensor variations
        self.room_states = {
            "living room": {"humidity": 50, "light": 600},
            "bedroom": {"humidity": 55, "light": 400}
        }
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client connects to the broker"""
        if rc == 0:
            print(f"✓ Connected to MQTT Broker: {MQTT_BROKER}")
            self.is_connected = True
        else:
            print(f"✗ Failed to connect, return code {rc}")
            self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the broker"""
        if rc != 0:
            print(f"✗ Unexpected disconnection. Return code: {rc}")
        self.is_connected = False
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection
            return self.is_connected
        except Exception as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def generate_sensor_data(self, room):
        """Generate mock sensor data with small variations"""
        current_state = self.room_states[room]
        
        # Add small random fluctuations for smooth variation
        humidity_variation = random.uniform(-1, 1)  # ±1% variation
        light_variation = random.uniform(-15, 15)   # ±15 light units variation
        
        humidity = max(20, min(95, current_state["humidity"] + humidity_variation))
        light = max(50, min(1023, current_state["light"] + light_variation))
        
        # Update state for next iteration
        self.room_states[room]["humidity"] = humidity
        self.room_states[room]["light"] = light
        
        return round(humidity, 1), int(light)
    
    def publish_sensor_data(self):
        """Publish mock sensor data to MQTT"""
        if not self.is_connected:
            print("✗ Not connected to MQTT broker")
            return False
        
        # Publish data only for living room
        room = "living room"
        humidity, light_level = self.generate_sensor_data(room)
        
        # Format: "room,humidity,light_level" for better flexibility
        payload = f"{room},{humidity},{light_level}"
        
        try:
            result = self.client.publish(MQTT_TOPIC_SENSORS, payload)
            
            if result.rc == 0:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ✓ {room:15} | humidity={humidity}%, light={light_level}")
                return True
            else:
                print(f"✗ Publish failed for {room} with return code {result.rc}")
                return False
        except Exception as e:
            print(f"✗ Publish error for {room}: {e}")
            return False
    
    def start_publishing(self, interval=SENSOR_UPDATE_INTERVAL):
        """Start publishing mock sensor data at regular intervals"""
        print(f"\n🌐 Mock Sensor Publisher Started")
        print(f"   Broker: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"   Topic: {MQTT_TOPIC_SENSORS}")
        print(f"   Interval: {interval} seconds")
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
        """Stop the publisher and disconnect from broker"""
        self.client.loop_stop()
        self.client.disconnect()
        print("✓ Disconnected from MQTT broker")


def main():
    publisher = MockSensorPublisher()
    
    # Connect to broker
    if publisher.connect():
        # Start publishing mock data
        publisher.start_publishing()
    else:
        print("✗ Failed to establish MQTT connection")


if __name__ == "__main__":
    main()
