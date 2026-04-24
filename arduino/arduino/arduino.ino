#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <ArduinoJson.h>

// --- WiFi & MQTT Configuration ---
const char* ssid = "S1003 1821 2.4G";
const char* password = "0981134979";

const char* mqtt_server = "theanh0410.cloud.shiftr.io";
const int   mqtt_port = 1883;   // non-secure (no TLS)
const char* mqtt_user = "theanh0410";
const char* mqtt_password = "eoCNam4gR2IWOA6d";

// Make client id unique per board
String mqtt_client_id;

// --- MQTT Topics ---
const char* topicControl = "home/control";
const char* topicSensors = "home/sensors"; // (not used yet, kept for compatibility)

// --- Sensor & Actuator Pins (ESP8266) ---
// NodeMCU pins:
// D1=GPIO5, D2=GPIO4, D4=GPIO2, D5=GPIO14, D6=GPIO12, D7=GPIO13
// Avoid D3(GPIO0) and D8(GPIO15) for normal outputs (boot strap pins).

#define DHTPIN  D4        // GPIO2 (OK if you don't force it LOW at boot)
#define DHTTYPE DHT11

#define LIGHT1_PIN D1     // GPIO5
#define LIGHT2_PIN D2     // GPIO4
#define FAN1_PIN   D5     // GPIO14
#define FAN2_PIN   D6     // GPIO12

// ESP8266 has only A0 (0-1V) for analog input.
// If you had ESP32 pin 34 as light sensor analog, you must rewire to A0 + correct scaling.
#define LIGHT_SENSOR_PIN A0

DHT dht(DHTPIN, DHTTYPE);

WiFiClient espClient;
PubSubClient client(espClient);

// --- Function Prototypes ---
void reconnectMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void controlDevices(const String& cmd);

void setup() {
  Serial.begin(115200);
  delay(50);

  pinMode(LIGHT1_PIN, OUTPUT);
  pinMode(LIGHT2_PIN, OUTPUT);
  pinMode(FAN1_PIN, OUTPUT);
  pinMode(FAN2_PIN, OUTPUT);

  // default OFF
  digitalWrite(LIGHT1_PIN, LOW);
  digitalWrite(LIGHT2_PIN, LOW);
  digitalWrite(FAN1_PIN, LOW);
  digitalWrite(FAN2_PIN, LOW);

  dht.begin();

  // Connect WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  int attempt = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    attempt++;
    if (attempt > 30) {
      Serial.println("\nWiFi connection failed!");
      // Don't return forever; keep trying in loop() instead
      break;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  }

  // MQTT setup
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  client.setKeepAlive(60);
  client.setSocketTimeout(10);
  client.setBufferSize(256);

  // unique client id
  mqtt_client_id = "esp8266_" + String(ESP.getChipId(), HEX);

  reconnectMQTT();
}

void loop() {
  // ensure WiFi
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.disconnect();
    WiFi.begin(ssid, password);
    delay(500);
  }

  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT as ");
    Serial.print(mqtt_client_id);
    Serial.print(" ... ");

    if (client.connect(mqtt_client_id.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected!");
      client.subscribe(topicControl);
      Serial.print("Subscribed: ");
      Serial.println(topicControl);
    } else {
      Serial.print("failed, rc=");
      Serial.println(client.state());
      delay(2000);
    }
  }
}

// void mqttCallback(char* topic, byte* payload, unsigned int length) {
//   // Copy payload safely (DON'T do payload[length] = '\0' because payload isn't yours)
//   char buf[128];
//   unsigned int n = (length < sizeof(buf) - 1) ? length : (sizeof(buf) - 1);
//   memcpy(buf, payload, n);
//   buf[n] = '\0';

//   String command = String(buf);
//   command.trim();
//   command.toLowerCase();

//   Serial.print("Received [");
//   Serial.print(topic);
//   Serial.print("]: ");
//   Serial.println(command);

//   if (String(topic) == topicControl) {
//     controlDevices(command);
//   }
// }

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  char buf[256];
  unsigned int n = (length < sizeof(buf) - 1) ? length : (sizeof(buf) - 1);
  memcpy(buf, payload, n);
  buf[n] = '\0';

  String message = String(buf);
  message.trim();

  Serial.print("Received [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.println(message);

  if (String(topic) == topicControl) {
    // If payload looks like JSON, parse it
    if (message.startsWith("{")) {
      DynamicJsonDocument doc(256);
      DeserializationError error = deserializeJson(doc, message);

      if (error) {
        Serial.print("JSON parse failed: ");
        Serial.println(error.c_str());
        return;
      }

      String device = doc["device"] | "";
      String action = doc["action"] | "";
      String room   = doc["room"] | "";
      bool valid    = doc["valid"] | false;

      device.toLowerCase();
      action.toLowerCase();
      room.toLowerCase();

      if (!valid) {
        Serial.println("Ignoring invalid command");
        return;
      }

      handleJsonCommand(device, action, room);
    } 
    else {
      // Old plain text command
      message.toLowerCase();
      controlDevices(message);
    }
  }
}

void handleJsonCommand(const String& device, const String& action, const String& room) {
  // Living room light
  if (room == "living room" && device == "light") {
    if (action == "turn on" || action == "open" || action == "switch on") {
      digitalWrite(LIGHT1_PIN, HIGH);
      Serial.println("Living room light ON");
    } 
    else if (action == "turn off" || action == "close" || action == "switch off") {
      digitalWrite(LIGHT1_PIN, LOW);
      Serial.println("Living room light OFF");
    }
  }

  // Bedroom light
  else if (room == "bedroom" && device == "light") {
    if (action == "turn on" || action == "open" || action == "switch on") {
      digitalWrite(LIGHT2_PIN, HIGH);
      Serial.println("Bedroom light ON");
    } 
    else if (action == "turn off" || action == "close" || action == "switch off") {
      digitalWrite(LIGHT2_PIN, LOW);
      Serial.println("Bedroom light OFF");
    }
  }

  // Living room fan
  else if (room == "living room" && device == "fan") {
    if (action == "turn on" || action == "open" || action == "switch on") {
      digitalWrite(FAN1_PIN, HIGH);
      Serial.println("Living room fan ON");
    } 
    else if (action == "turn off" || action == "close" || action == "switch off") {
      digitalWrite(FAN1_PIN, LOW);
      Serial.println("Living room fan OFF");
    }
  }

  // Bedroom fan
  else if (room == "bedroom" && device == "fan") {
    if (action == "turn on" || action == "open" || action == "switch on") {
      digitalWrite(FAN2_PIN, HIGH);
      Serial.println("Bedroom fan ON");
    } 
    else if (action == "turn off" || action == "close" || action == "switch off") {
      digitalWrite(FAN2_PIN, LOW);
      Serial.println("Bedroom fan OFF");
    }
  }

  else {
    Serial.println("Unknown JSON command");
  }
}

void controlDevices(const String& cmd) {
  // Living room light
  if (cmd == "livingroom_light_on" || cmd == "light1_on") {
    digitalWrite(LIGHT1_PIN, HIGH);
    Serial.println("Living room light ON");
  } 
  else if (cmd == "livingroom_light_off" || cmd == "light1_off") {
    digitalWrite(LIGHT1_PIN, LOW);
    Serial.println("Living room light OFF");
  }

  // Bedroom light
  else if (cmd == "bedroom_light_on" || cmd == "light2_on") {
    digitalWrite(LIGHT2_PIN, HIGH);
    Serial.println("Bedroom light ON");
  } 
  else if (cmd == "bedroom_light_off" || cmd == "light2_off") {
    digitalWrite(LIGHT2_PIN, LOW);
    Serial.println("Bedroom light OFF");
  }

  // Living room fan
  else if (cmd == "livingroom_fan_on" || cmd == "fan1_on") {
    digitalWrite(FAN1_PIN, HIGH);
    Serial.println("Living room fan ON");
  } 
  else if (cmd == "livingroom_fan_off" || cmd == "fan1_off") {
    digitalWrite(FAN1_PIN, LOW);
    Serial.println("Living room fan OFF");
  }

  // Bedroom fan
  else if (cmd == "bedroom_fan_on" || cmd == "fan2_on") {
    digitalWrite(FAN2_PIN, HIGH);
    Serial.println("Bedroom fan ON");
  } 
  else if (cmd == "bedroom_fan_off" || cmd == "fan2_off") {
    digitalWrite(FAN2_PIN, LOW);
    Serial.println("Bedroom fan OFF");
  } 
  else {
    Serial.print("Unknown command: ");
    Serial.println(cmd);
  }
}