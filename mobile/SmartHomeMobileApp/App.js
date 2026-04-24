import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, Alert, TextInput, Dimensions, StatusBar } from 'react-native';
import 'react-native-url-polyfill/auto';
import mqtt from 'mqtt';
import { MaterialCommunityIcons, Ionicons, FontAwesome5 } from '@expo/vector-icons';
import io from 'socket.io-client';

// MQTT Configuration
const MQTT_BROKER = "wss://theanh0410.cloud.shiftr.io";
const MQTT_USER = "theanh0410";
const MQTT_PASSWORD = "eoCNam4gR2IWOA6d";
const CONTROL_TOPIC = "home/control";
const SENSOR_TOPIC = "home/sensors";

let client = null;
const { width, height } = Dimensions.get('window');

export default function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [humidity, setHumidity] = useState('--');
  const [lightLevel, setLightLevel] = useState('--');
  const [servoAngle, setServoAngle] = useState(90);
  const [dcSpeed, setDcSpeed] = useState(0);
  const [stepperRounds, setStepperRounds] = useState('1');
  const [deviceStates, setDeviceStates] = useState({
    light1: false,
    light2: false,
    fan1: false,
    fan2: false,
  });

  const socket = io('http://192.168.0.105:5000/'); 

  useEffect(() => {
    const options = {
      clientId: 'ExpoMobileClient_' + Math.random().toString(36).substr(2, 9),
      username: MQTT_USER,
      password: MQTT_PASSWORD,
      clean: true,
      connectTimeout: 4000,
      reconnectPeriod: 1000,
    };

    client = mqtt.connect(MQTT_BROKER, options);

    client.on('connect', () => {
      console.log('Connected to MQTT Broker');
      setIsConnected(true);
      client.subscribe(SENSOR_TOPIC, { qos: 0 });
      client.subscribe(CONTROL_TOPIC, { qos: 0 });  // Subscribe to control topic for device status updates
    });

    client.on('error', (error) => {
      console.log('MQTT Error:', error);
      setIsConnected(false);
    });

    client.on('offline', () => {
      console.log('MQTT Offline');
      setIsConnected(false);
    });

    // Handle incoming messages for device states and sensor data
    client.on('message', (topic, message) => {
      if (topic === SENSOR_TOPIC) {
        const payload = message.toString();
        const [hum, light] = payload.split(',');
        setHumidity(hum || '--');
        setLightLevel(light || '--');
      }
      
      if (topic === CONTROL_TOPIC) {
        const command = message.toString();
        const [device, status] = command.split('_');
        
        // Update the state of the device based on the command received
        setDeviceStates(prev => ({ ...prev, [device]: status === 'on' }));
      }
    });

    // Listen for device state changes from Flask (via Socket.IO)
    socket.on('device_status', (data) => {
      const { command } = data;
      const [device, status] = command.split('_');
      setDeviceStates(prev => ({ ...prev, [device]: status === 'on' }));
    });

    return () => {
      socket.off('device_status');
      if (client) {
        client.end();
      }
    };
  }, []);

  // Publish command to MQTT broker
  const sendCommand = (command) => {
    if (isConnected && client) {
      client.publish(CONTROL_TOPIC, command, { qos: 0, retain: false });
      console.log(`Published command: ${command}`);
    } else {
      Alert.alert("Lỗi kết nối", "Không thể gửi lệnh, vui lòng kiểm tra kết nối MQTT.");
    }
  };

  // Toggle device on/off
  const toggleDevice = (device, action) => {
    const newState = action === 'on';
    setDeviceStates(prev => ({ ...prev, [device]: newState }));
    sendCommand(`${device}_${action}`);
  };

  // Handle motor controls (servo, DC motor, stepper)
  const handleServoAngleChange = (angle) => {
    setServoAngle(angle);
    sendCommand(`servo_${angle}`);
  };

  const handleDcSpeedChange = (speed) => {
    setDcSpeed(speed);
    sendCommand(`dc_motor_speed_${speed}`);
  };

  const handleStepperCommand = (direction) => {
    const rounds = stepperRounds || '1';
    if (parseInt(rounds) < 1) {
      Alert.alert("Giá trị không hợp lệ", "Số vòng phải lớn hơn hoặc bằng 1.");
      return;
    }
    const command = direction === 'cw' ? `step_motor_${rounds}` : `step_motor_c${rounds}`;
    sendCommand(command);
  };

  return (

    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Sensor Cards */}
        <View style={styles.sensorContainer}>
          <View style={styles.sensorCard}>
            <View style={styles.sensorIconContainer}>
              <MaterialCommunityIcons name="water-percent" size={24} color="#4FC3F7" />
            </View>
            <Text style={styles.sensorLabel}>Độ ẩm</Text>
            <Text style={styles.sensorValue}>{humidity}%</Text>
          </View>
          
          <View style={styles.sensorCard}>
            <View style={styles.sensorIconContainer}>
              <MaterialCommunityIcons name="brightness-6" size={24} color="#FFB74D" />
            </View>
            <Text style={styles.sensorLabel}>Ánh sáng</Text>
            <Text style={styles.sensorValue}>{lightLevel}</Text>
          </View>
        </View>

        {/* Light and Fan Controls */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Đèn</Text>
          <View style={styles.deviceGrid}>
            {['light1', 'light2'].map((device, index) => (
              <TouchableOpacity
                key={device}
                style={[
                  styles.deviceCard,
                  { backgroundColor: deviceStates[device] ? '#FFD54F' : '#2A2A3E' }
                ]}
                onPress={() => toggleDevice(device, deviceStates[device] ? 'off' : 'on')}
              >
                <MaterialCommunityIcons
                  name={deviceStates[device] ? "lightbulb-on" : "lightbulb-off"}
                  size={32}
                  color={deviceStates[device] ? '#333' : '#fff'}
                />
                <Text style={[styles.deviceName, { color: deviceStates[device] ? '#333' : '#fff' }]}>
                  Đèn {index + 1}
                </Text>
                <Text style={[styles.deviceStatus, { color: deviceStates[device] ? '#333' : '#888' }]}>
                  {deviceStates[device] ? 'Đang bật' : 'Đã tắt'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Fan Controls */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quạt</Text>
          <View style={styles.deviceGrid}>
            {['fan1', 'fan2'].map((device, index) => (
              <TouchableOpacity
                key={device}
                style={[
                  styles.deviceCard,
                  { backgroundColor: deviceStates[device] ? '#81C784' : '#2A2A3E' }
                ]}
                onPress={() => toggleDevice(device, deviceStates[device] ? 'off' : 'on')}
              >
                <MaterialCommunityIcons
                  name="fan"
                  size={32}
                  color={deviceStates[device] ? '#333' : '#fff'}
                />
                <Text style={[styles.deviceName, { color: deviceStates[device] ? '#333' : '#fff' }]}>
                  Quạt {index + 1}
                </Text>
                <Text style={[styles.deviceStatus, { color: deviceStates[device] ? '#333' : '#888' }]}>
                  {deviceStates[device] ? 'Đang chạy' : 'Đã dừng'}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#16213E',
  },
  headerContainer: {
    backgroundColor: '#1a1a2e',
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  iconContainer: {
    backgroundColor: '#0F3460',
    padding: 12,
    borderRadius: 12,
    marginRight: 15,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#fff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#B8B8D4',
  },
  connectionStatus: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  sensorContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  sensorCard: {
    backgroundColor: '#1E2749',
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
    width: (width - 60) / 2,
    borderWidth: 1,
    borderColor: '#2A2A3E',
  },
  sensorIconContainer: {
    backgroundColor: '#0F3460',
    padding: 12,
    borderRadius: 12,
    marginBottom: 10,
  },
  sensorLabel: {
    fontSize: 14,
    color: '#B8B8D4',
    marginBottom: 5,
  },
  sensorValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  section: {
    marginBottom: 30,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 15,
  },
  deviceGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  deviceCard: {
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
    width: (width - 60) / 2,
    minHeight: 120,
    justifyContent: 'center',
  },
  deviceName: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 10,
  },
  deviceStatus: {
    fontSize: 12,
    marginTop: 5,
  },
  servoContainer: {
    backgroundColor: '#1E2749',
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2A2A3E',
  },
  servoDisplay: {
    alignItems: 'center',
    marginBottom: 20,
  },
  servoAngle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginTop: 10,
  },
  servoButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  servoButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
    minWidth: 80,
    alignItems: 'center',
  },
  servoButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  dcMotorContainer: {
    backgroundColor: '#1E2749',
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2A2A3E',
  },
  dcMotorDisplay: {
    alignItems: 'center',
    marginBottom: 20,
  },
  dcMotorSpeed: {
    fontSize: 18,
    color: '#fff',
    marginTop: 10,
  },
  dcMotorButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  dcMotorButton: {
    backgroundColor: '#7E57C2',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
    minWidth: 100,
    alignItems: 'center',
  },
  dcMotorButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  stepperContainer: {
    backgroundColor: '#1E2749',
    padding: 20,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#2A2A3E',
  },
  stepperInput: {
    backgroundColor: '#2A2A3E',
    color: '#fff',
    padding: 15,
    borderRadius: 12,
    fontSize: 16,
    marginBottom: 20,
    textAlign: 'center',
  },
  stepperButtons: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  stepperButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    alignItems: 'center',
    flexDirection: 'row',
    minWidth: 100,
    justifyContent: 'center',
  },
  stepperButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
});