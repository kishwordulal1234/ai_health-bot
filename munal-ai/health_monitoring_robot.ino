#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <NewPing.h>

// LCD Configuration
LiquidCrystal_I2C lcd(0x27, 16, 2);  // I2C address 0x27, 16 columns, 2 rows

// Custom characters for ECG graph
byte customChar[8][8] = {
  { // 0: Baseline
    B00000,
    B00000,
    B00000,
    B00100,
    B00000,
    B00000,
    B00000,
    B00000
  },
  { // 1: Small up
    B00000,
    B00000,
    B00100,
    B00000,
    B00000,
    B00000,
    B00000,
    B00000
  },
  { // 2: Medium up
    B00000,
    B00100,
    B00000,
    B00000,
    B00000,
    B00000,
    B00000,
    B00000
  },
  { // 3: Big spike up
    B00100,
    B01110,
    B00100,
    B00000,
    B00000,
    B00000,
    B00000,
    B00000
  },
  { // 4: Small down
    B00000,
    B00000,
    B00000,
    B00000,
    B00100,
    B00000,
    B00000,
    B00000
  },
  { // 5: Medium down
    B00000,
    B00000,
    B00000,
    B00000,
    B00000,
    B00100,
    B00000,
    B00000
  },
  { // 6: Big spike down
    B00000,
    B00000,
    B00000,
    B00000,
    B00100,
    B01110,
    B00100,
    B00000
  },
  { // 7: Flatline
    B00000,
    B00000,
    B00000,
    B00000,
    B11111,
    B00000,
    B00000,
    B00000
  }
};

// Ultrasonic Sensors Pins (Mega pins)
#define FRONT_TRIG_PIN 22
#define FRONT_ECHO_PIN 23
#define RIGHT_TRIG_PIN 24
#define RIGHT_ECHO_PIN 25
#define BACK_TRIG_PIN 26
#define BACK_ECHO_PIN 27
#define LEFT_TRIG_PIN 28
#define LEFT_ECHO_PIN 29

#define MAX_DISTANCE 400  // Maximum distance for ultrasonic sensors (in cm)

// Motor Driver Pins (Mega pins)
#define MOTOR_A1 8  // Left Motor
#define MOTOR_A2 9
#define MOTOR_B1 10  // Right Motor
#define MOTOR_B2 11

// Sensor Pins (Analog pins on Mega)
#define HEARTBEAT_PIN A0
#define MOISTURE_PIN A1
#define TEMP_PIN A2

// Constants
#define TARGET_DISTANCE 2000  // 20 meters in centimeters
#define MOTOR_SPEED 255      // Full speed for motors
#define SERIAL_BAUD_RATE 115200  // Higher baud rate for Mega
#define HEARTBEAT_THRESHOLD 550  // Adjust based on your sensor
#define TEMP_MIN 25.0   // Minimum valid temperature
#define TEMP_MAX 45.0   // Maximum valid temperature
#define MOISTURE_MIN 0  // Minimum valid moisture
#define MOISTURE_MAX 100 // Maximum valid moisture

// Communication timing
#define SENSOR_UPDATE_INTERVAL 50    // Update sensors every 50ms
#define SERIAL_UPDATE_INTERVAL 100   // Send data every 100ms
unsigned long lastSensorUpdate = 0;
unsigned long lastSerialUpdate = 0;
bool serialConnected = false;

// Error counters
int sensorErrors = 0;
int communicationErrors = 0;

// Create ultrasonic sensor objects
NewPing sonarFront(FRONT_TRIG_PIN, FRONT_ECHO_PIN, MAX_DISTANCE);
NewPing sonarRight(RIGHT_TRIG_PIN, RIGHT_ECHO_PIN, MAX_DISTANCE);
NewPing sonarBack(BACK_TRIG_PIN, BACK_ECHO_PIN, MAX_DISTANCE);
NewPing sonarLeft(LEFT_TRIG_PIN, LEFT_ECHO_PIN, MAX_DISTANCE);

// Variables for health monitoring
int heartRate = 0;
int moistureLevel = 0;
float temperature = 0.0;
unsigned long lastHeartbeatTime = 0;
int heartbeatCount = 0;
unsigned long startTime = 0;

// ECG wave pattern (P-QRS-T wave)
const byte ECG_PATTERN[] = {0,1,0,0,3,6,0,1,0,0,0,0,1,0,0,0};
const int PATTERN_LENGTH = 16;
int patternIndex = 0;

void setup() {
  // Initialize LCD
  lcd.init();
  lcd.backlight();
  
  // Initialize custom characters
  for(int i = 0; i < 8; i++) {
    lcd.createChar(i, customChar[i]);
  }
  
  // Initialize motor pins
  pinMode(MOTOR_A1, OUTPUT);
  pinMode(MOTOR_A2, OUTPUT);
  pinMode(MOTOR_B1, OUTPUT);
  pinMode(MOTOR_B2, OUTPUT);
  
  // Initialize Serial with higher baud rate
  Serial.begin(SERIAL_BAUD_RATE);
  while (!Serial) {
    ; // Wait for serial port to connect
  }
  serialConnected = true;
  
  // Display startup message
  displayStatus("System Starting", "Connecting...");
  delay(1000);
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Update sensors at regular interval
  if (currentMillis - lastSensorUpdate >= SENSOR_UPDATE_INTERVAL) {
    lastSensorUpdate = currentMillis;
    readHealthSensors();
    updateECGGraph();
    displayHealthInfo();
    checkObstaclesAndMove();
  }
  
  // Send data at regular interval
  if (currentMillis - lastSerialUpdate >= SERIAL_UPDATE_INTERVAL) {
    lastSerialUpdate = currentMillis;
    sendSensorData();
  }
  
  // Check for serial connection
  if (!Serial && serialConnected) {
    serialConnected = false;
    displayStatus("Error:", "Serial Lost");
  } else if (Serial && !serialConnected) {
    serialConnected = true;
    displayStatus("Connected", "Serial OK");
    delay(1000);
  }
}

void displayStatus(const char* line1, const char* line2) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print(line1);
  lcd.setCursor(0, 1);
  lcd.print(line2);
}

void readHealthSensors() {
  // Read and validate heart rate
  int rawValue = analogRead(HEARTBEAT_PIN);
  if (rawValue > HEARTBEAT_THRESHOLD) {
    if (millis() - lastHeartbeatTime > 50) {
      heartbeatCount++;
      lastHeartbeatTime = millis();
      patternIndex = 0;
    }
  }
  
  // Calculate heart rate every 10 seconds
  if (millis() - startTime >= 10000) {
    heartRate = heartbeatCount * 6;
    // Validate heart rate
    if (heartRate > 220 || heartRate < 30) {
      heartRate = 0;  // Invalid reading
      sensorErrors++;
    }
    heartbeatCount = 0;
    startTime = millis();
  }
  
  // Read and validate moisture level
  int rawMoisture = analogRead(MOISTURE_PIN);
  moistureLevel = map(rawMoisture, 0, 1023, 0, 100);
  if (moistureLevel < MOISTURE_MIN || moistureLevel > MOISTURE_MAX) {
    moistureLevel = 0;  // Invalid reading
    sensorErrors++;
  }
  
  // Read and validate temperature
  int tempReading = analogRead(TEMP_PIN);
  float rawTemp = (tempReading * 5.0 * 100.0) / 1024.0;
  if (rawTemp >= TEMP_MIN && rawTemp <= TEMP_MAX) {
    temperature = rawTemp;
  } else {
    temperature = 0;  // Invalid reading
    sensorErrors++;
  }
}

void updateECGGraph() {
  lcd.setCursor(0, 0);
  
  // Display the ECG pattern
  for(int i = 0; i < 16; i++) {
    int displayIndex = (patternIndex + i) % PATTERN_LENGTH;
    lcd.write(ECG_PATTERN[displayIndex]);
  }
  
  // Only advance pattern if we detect a heartbeat or enough time has passed
  if (millis() - lastHeartbeatTime > 1000) {
    patternIndex = (patternIndex + 1) % PATTERN_LENGTH;
  }
}

void displayHealthInfo() {
  // Display health info on second row
  lcd.setCursor(0, 1);
  lcd.print("HR:");
  lcd.print(heartRate);
  lcd.print(" T:");
  lcd.print(temperature, 1);
  lcd.print("C ");
  lcd.print(moistureLevel);
  lcd.print("%");
}

void sendSensorData() {
  if (!serialConnected) return;
  
  // Create JSON string with error counts
  String jsonData = "{";
  jsonData += "\"heart_rate\":" + String(heartRate) + ",";
  jsonData += "\"temperature\":" + String(temperature, 1) + ",";
  jsonData += "\"moisture\":" + String(moistureLevel) + ",";
  jsonData += "\"raw_heartbeat\":" + String(analogRead(HEARTBEAT_PIN)) + ",";
  jsonData += "\"sensor_errors\":" + String(sensorErrors) + ",";
  jsonData += "\"comm_errors\":" + String(communicationErrors);
  jsonData += "}";
  
  // Try to send data
  if (Serial.println(jsonData)) {
    // Data sent successfully
    if (communicationErrors > 0) communicationErrors--;
  } else {
    communicationErrors++;
    serialConnected = false;
  }
}

void checkObstaclesAndMove() {
  int frontDist = sonarFront.ping_cm();
  int rightDist = sonarRight.ping_cm();
  int backDist = sonarBack.ping_cm();
  int leftDist = sonarLeft.ping_cm();
  
  // Check if any sensor detects an object within range
  if (frontDist > 0 && frontDist < TARGET_DISTANCE) {
    moveForward();
  } else if (rightDist > 0 && rightDist < TARGET_DISTANCE) {
    turnRight();
  } else if (backDist > 0 && backDist < TARGET_DISTANCE) {
    moveBackward();
  } else if (leftDist > 0 && leftDist < TARGET_DISTANCE) {
    turnLeft();
  } else {
    stopMotors();
  }
}

void moveForward() {
  digitalWrite(MOTOR_A1, HIGH);
  digitalWrite(MOTOR_A2, LOW);
  digitalWrite(MOTOR_B1, HIGH);
  digitalWrite(MOTOR_B2, LOW);
}

void moveBackward() {
  digitalWrite(MOTOR_A1, LOW);
  digitalWrite(MOTOR_A2, HIGH);
  digitalWrite(MOTOR_B1, LOW);
  digitalWrite(MOTOR_B2, HIGH);
}

void turnRight() {
  digitalWrite(MOTOR_A1, HIGH);
  digitalWrite(MOTOR_A2, LOW);
  digitalWrite(MOTOR_B1, LOW);
  digitalWrite(MOTOR_B2, HIGH);
}

void turnLeft() {
  digitalWrite(MOTOR_A1, LOW);
  digitalWrite(MOTOR_A2, HIGH);
  digitalWrite(MOTOR_B1, HIGH);
  digitalWrite(MOTOR_B2, LOW);
}

void stopMotors() {
  digitalWrite(MOTOR_A1, LOW);
  digitalWrite(MOTOR_A2, LOW);
  digitalWrite(MOTOR_B1, LOW);
  digitalWrite(MOTOR_B2, LOW);
}
