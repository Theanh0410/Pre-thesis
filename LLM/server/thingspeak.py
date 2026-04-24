import requests
import json
import logging
import time
from datetime import datetime

logging.basicConfig(
    filename="thingspeak_integration.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

THINGSPEAK_WRITE_URL = "https://api.thingspeak.com/update"
THINGSPEAK_API_KEY = "Y3MBPOB3SCCN8HJC"  

def upload_to_thingspeak(thingspeak_data, api_key):
    object_map = {"light": 1, "fan": 2}  
    action_map = {"Turn on": 1, "Turn off": 0} 
    
    object_value = object_map.get(thingspeak_data["device"], 0)
    action_value = action_map.get(thingspeak_data["action"], 0)
    
    params = {
        "api_key": api_key,
        "field1": object_value,
        "field2": action_value,
        "field3": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    response = requests.get("https://api.thingspeak.com/update", params=params)
    print(f"ThingSpeak response: {response.status_code}, {response.text}")
    return response.status_code == 200