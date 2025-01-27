# Health Monitoring Robot - Setup and Usage Guide

## Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Hardware Assembly](#hardware-assembly)
4. [Software Setup](#software-setup)
5. [Running the System](#running-the-system)
6. [Troubleshooting](#troubleshooting)

## Hardware Requirements

### Main Components
1. Arduino Mega 2560
2. Raspberry Pi 4 (any model)
3. 16x2 LCD Display with I2C Module
4. L298N Motor Driver
5. 2x DC Motors
6. 4x Ultrasonic Sensors (HC-SR04)
7. Heart Rate Sensor (KY-039)
8. Temperature Sensor (LM35)
9. Soil Moisture Sensor (used for body moisture)
10. USB-A to USB-B Cable (for Arduino-Raspberry Pi connection)

### Power Supply
- 12V Power Supply for Motors
- 5V Power Supply for Arduino (via USB or DC jack)
- 5V Power Supply for Raspberry Pi

### Additional Components
- Breadboard
- Jumper Wires (male-to-male, male-to-female)
- 100μF and 0.1μF capacitors for power filtering
- Mounting hardware and chassis for the robot

## Software Requirements

### Raspberry Pi Setup
1. Raspberry Pi OS (latest version)
2. Python 3.7 or higher
3. Required Python packages:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip
   pip3 install flask
   pip3 install pyserial
   pip3 install google-generativeai
   ```

### Arduino Setup
1. Arduino IDE (2.0 or higher)
2. Required Libraries:
   - Wire.h (built-in)
   - LiquidCrystal_I2C
   - NewPing

## Hardware Assembly

### 1. LCD Display Connection
- VCC → 5V
- GND → GND
- SDA → Pin 20 (SDA)
- SCL → Pin 21 (SCL)

### 2. Ultrasonic Sensors
#### Front Sensor
- VCC → 5V
- GND → GND
- TRIG → Pin 22
- ECHO → Pin 23

#### Right Sensor
- VCC → 5V
- GND → GND
- TRIG → Pin 24
- ECHO → Pin 25

#### Back Sensor
- VCC → 5V
- GND → GND
- TRIG → Pin 26
- ECHO → Pin 27

#### Left Sensor
- VCC → 5V
- GND → GND
- TRIG → Pin 28
- ECHO → Pin 29

### 3. Motor Driver (L298N)
- ENA → Jumpered for full speed
- IN1 → Pin 8
- IN2 → Pin 9
- IN3 → Pin 10
- IN4 → Pin 11
- ENB → Jumpered for full speed
- 12V → External power supply positive
- GND → Common ground

### 4. Health Sensors
#### Heart Rate Sensor (KY-039)
- VCC → 5V
- GND → GND
- Signal → A0

#### Body Moisture Sensor
- VCC → 5V
- GND → GND
- Signal → A1

#### Temperature Sensor (LM35)
- VCC → 5V
- GND → GND
- Signal → A2

## Software Setup

### 1. Arduino Setup
1. Install Arduino IDE
2. Install Required Libraries:
   - Open Arduino IDE
   - Go to Tools → Manage Libraries
   - Search and install:
     - "LiquidCrystal I2C"
     - "NewPing"

3. Upload Code:
   - Open `health_monitoring_robot.ino`
   - Select Board: "Arduino Mega 2560"
   - Select correct COM port
   - Click Upload

### 2. Raspberry Pi Setup
1. Copy project files to Raspberry Pi:
   ```bash
   git clone <repository-url>
   cd munal-ai
   ```

2. Install dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export GEMINI_API_KEY="your_api_key_here"
   ```

## Running the System

### 1. Initial Setup
1. Power up the Arduino Mega with 12V supply
2. Connect Arduino to Raspberry Pi via USB
3. Power up Raspberry Pi
4. Wait for LCD to show "System Starting"

### 2. Starting the Application
1. On Raspberry Pi, open terminal:
   ```bash
   cd munal-ai
   python3 munal.py
   ```

2. Access the web interface:
   - Open browser on any device in the same network
   - Go to: `http://<raspberry-pi-ip>:5000`

### 3. Using the System
1. The LCD will show:
   - Top row: ECG graph
   - Bottom row: Heart rate, temperature, moisture

2. Web Interface:
   - Enter patient information
   - Add symptoms
   - Get AI-powered analysis
   - View real-time sensor data

## Troubleshooting

### Common Issues

1. **Arduino Not Detected**
   - Check USB connection
   - Verify correct COM port
   - Try different USB cable
   - Check if Arduino shows "Serial Lost" on LCD

2. **Sensor Errors**
   - Check all connections
   - Verify power supply voltages
   - Monitor error counts in serial output
   - Check sensor placement

3. **Communication Issues**
   - Restart Raspberry Pi
   - Check if Flask server is running
   - Verify network connection
   - Check serial port permissions

### LED Status Indicators
- LCD showing "Serial OK": System working normally
- LCD showing "Serial Lost": Communication error
- LCD showing "Error": Sensor or system error

### Getting Help
- Check serial monitor for detailed error messages
- Monitor error counters in JSON output
- Verify all connections match the guide
- Check power supply voltages

For additional support or questions, please refer to the project repository or contact support.
