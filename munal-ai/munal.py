from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
import json
import time
import serial
import serial.tools.list_ports
import threading
from queue import Queue
import glob
import sys

app = Flask(__name__)
app.secret_key = '7894'

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAZm5Ic35EtPA50MaEIxeFFHLBTw0VjQlM"
genai.configure(api_key=GEMINI_API_KEY)

try:
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    model = None

# Global variables for Arduino data
arduino_data = {
    "heart_rate": 0,
    "temperature": 0.0,
    "moisture": 0,
    "raw_heartbeat": 0
}
arduino_data_lock = threading.Lock()
serial_port = None

def find_arduino_port():
    """Find the Arduino Mega serial port on Raspberry Pi"""
    if sys.platform.startswith('linux'):  # Raspberry Pi
        # Look for USB serial devices
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')
        
        if not ports:
            print("No USB serial devices found")
            return None
            
        # If multiple ports found, try each one
        for port in ports:
            try:
                # Try to open the port
                ser = serial.Serial(port, 9600, timeout=1)
                ser.close()
                print(f"Found Arduino Mega on {port}")
                return port
            except:
                continue
                
        print("No Arduino Mega found")
        return None
    else:  # Windows/Other OS (for development)
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if "Arduino" in port.description or "CH340" in port.description:
                return port.device
        return None

def read_arduino_data():
    """Read data from Arduino in a separate thread"""
    global serial_port, arduino_data
    
    while True:  # Keep trying to connect
        try:
            port = find_arduino_port()
            if port:
                serial_port = serial.Serial(port, 9600, timeout=1)
                print(f"Connected to Arduino Mega on {port}")
                
                # Main reading loop
                while True:
                    if serial_port.in_waiting:
                        try:
                            line = serial_port.readline().decode('utf-8').strip()
                            if line:
                                data = json.loads(line)
                                with arduino_data_lock:
                                    arduino_data.update(data)
                        except json.JSONDecodeError as e:
                            print(f"JSON parsing error: {e}")
                        except Exception as e:
                            print(f"Error reading data: {e}")
                            break  # Break inner loop to reconnect
                    time.sleep(0.1)
            else:
                print("Arduino Mega not found. Retrying in 5 seconds...")
                time.sleep(5)
                
        except Exception as e:
            print(f"Connection error: {e}")
            if serial_port:
                try:
                    serial_port.close()
                except:
                    pass
            time.sleep(5)  # Wait before retrying

# Start Arduino reading thread
arduino_thread = threading.Thread(target=read_arduino_data, daemon=True)
arduino_thread.start()

# Your HTML_TEMPLATE remains the same as before
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Medical Symptom Analyzer</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" rel="stylesheet">
    <style>
        .loader {
            border: 5px solid #f3f3f3;
            border-radius: 50%;
            border-top: 5px solid #3498db;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .overlay {
            background-color: rgba(0, 0, 0, 0.5);
            z-index: 50;
        }

        .symptom-tag {
            transition: all 0.3s ease;
        }

        .symptom-tag:hover {
            transform: translateY(-2px);
        }

        .progress-step {
            transition: all 0.3s ease;
        }

        .progress-step.active {
            transform: scale(1.1);
        }

        .custom-shadow {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body class="bg-gradient-to-br from-blue-50 to-blue-100 min-h-screen">
    <!-- Progress Bar -->
    <div class="fixed top-0 left-0 right-0 bg-white shadow-md z-40">
        <div class="container mx-auto px-4 py-3">
            <div class="flex justify-between items-center">
                <div id="progressSteps" class="flex space-x-4">
                    <div class="progress-step flex items-center">
                        <div class="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center">1</div>
                        <span class="ml-2 text-sm">Patient Info</span>
                    </div>
                    <div class="progress-step flex items-center opacity-50">
                        <div class="w-8 h-8 rounded-full bg-gray-300 text-white flex items-center justify-center">2</div>
                        <span class="ml-2 text-sm">Symptoms</span>
                    </div>
                    <div class="progress-step flex items-center opacity-50">
                        <div class="w-8 h-8 rounded-full bg-gray-300 text-white flex items-center justify-center">3</div>
                        <span class="ml-2 text-sm">Analysis</span>
                    </div>
                </div>
                <button id="helpBtn" class="text-blue-500 hover:text-blue-700">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <!-- Loading Overlay -->
    <div id="loadingOverlay" class="hidden fixed inset-0 overlay flex items-center justify-center">
        <div class="bg-white p-8 rounded-lg shadow-lg text-center animate__animated animate__fadeIn">
            <div class="loader mx-auto mb-4"></div>
            <p class="text-lg font-semibold">Analyzing symptoms...</p>
            <p class="text-sm text-gray-600">Processing your health information</p>
        </div>
    </div>

    <!-- Help Modal -->
    <div id="helpModal" class="hidden fixed inset-0 overlay flex items-center justify-center z-50">
        <div class="bg-white p-8 rounded-lg shadow-lg max-w-md animate__animated animate__fadeInDown">
            <h3 class="text-xl font-bold mb-4">How to Use the Analyzer</h3>
            <ol class="list-decimal pl-5 space-y-2 mb-4">
                <li>Enter your basic information</li>
                <li>Add your symptoms one by one</li>
                <li>Use suggested symptoms or type your own</li>
                <li>Review the analysis results</li>
                <li>Save or print your report if needed</li>
            </ol>
            <button id="closeHelp" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 w-full">Got it!</button>
        </div>
    </div>

    <div class="container mx-auto px-4 py-20 max-w-2xl">
        <h1 class="text-4xl font-bold text-center mb-8 text-blue-600 animate__animated animate__fadeIn">
            🏥 Advanced Medical Symptom Analyzer
        </h1>
        
        <!-- Disclaimer -->
        <div class="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-8 animate__animated animate__fadeIn">
            <p class="text-yellow-700">
                ⚠️ <strong>DISCLAIMER:</strong> This is a prototype medical analysis tool. 
                The results should not be considered as professional medical advice. 
                Always consult with a qualified healthcare provider for proper diagnosis and treatment.
            </p>
        </div>

        <!-- Patient Information Section -->
        <div id="nameSection" class="bg-white shadow-lg rounded-lg px-8 pt-6 pb-8 mb-4 animate__animated animate__fadeIn">
            <h2 class="text-2xl font-semibold mb-6">Patient Information</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="patientName">
                        Full Name:
                    </label>
                    <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                           id="patientName" type="text" placeholder="Your name">
                </div>
                <div class="mb-4">
                    <label class="block text-gray-700 text-sm font-bold mb-2" for="patientAge">
                        Age:
                    </label>
                    <input class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                           id="patientAge" type="number" min="0" max="120" placeholder="Your age">
                </div>
            </div>
            <div class="mb-4">
                <label class="block text-gray-700 text-sm font-bold mb-2">Gender:</label>
                <div class="flex space-x-4">
                    <label class="inline-flex items-center">
                        <input type="radio" name="gender" value="male" class="form-radio">
                        <span class="ml-2">Male</span>
                    </label>
                    <label class="inline-flex items-center">
                        <input type="radio" name="gender" value="female" class="form-radio">
                        <span class="ml-2">Female</span>
                    </label>
                    <label class="inline-flex items-center">
                        <input type="radio" name="gender" value="other" class="form-radio">
                        <span class="ml-2">Other</span>
                    </label>
                </div>
            </div>
            <button id="submitName" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                Continue
            </button>
        </div>

        <!-- Symptoms Section -->
        <div id="symptomsSection" class="hidden bg-white shadow-lg rounded-lg px-8 pt-6 pb-8 mb-4">
            <h2 class="text-2xl font-semibold mb-6">Enter Your Symptoms</h2>
            
            <!-- Common Symptoms Quick Select -->
            <div class="mb-6">
                <h3 class="text-lg font-semibold mb-3">Common Symptoms:</h3>
                <div class="flex flex-wrap gap-2" id="commonSymptoms">
                    <button class="symptom-tag px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200">Headache</button>
                    <button class="symptom-tag px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200">Fever</button>
                    <button class="symptom-tag px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200">Cough</button>
                    <button class="symptom-tag px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200">Fatigue</button>
                    <button class="symptom-tag px-3 py-1 bg-blue-100 text-blue-700 rounded-full hover:bg-blue-200">Nausea</button>
                </div>
            </div>

            <div class="mb-4">
                <p class="text-gray-600 mb-2">Enter your symptoms (up to 7):</p>
                
                <!-- Symptom Input Methods Toggle -->
                <div class="mb-4">
                    <div class="flex space-x-4">
                        <button id="listModeBtn" class="bg-blue-500 text-white px-4 py-2 rounded-lg">List Mode</button>
                        <button id="paragraphModeBtn" class="bg-gray-300 text-gray-700 px-4 py-2 rounded-lg">Paragraph Mode</button>
                    </div>
                </div>

                <!-- List Mode Input -->
                <div id="listModeInput">
                    <div class="flex space-x-2">
                        <input class="flex-1 shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                               id="symptomInput" type="text" placeholder="Type or select a symptom">
                        <button id="micButton" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                            </svg>
                        </button>
                        <button id="addSymptom" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                            Add
                        </button>
                    </div>
                    <div id="micStatus" class="mt-2 text-sm text-gray-600 hidden">
                        Microphone is listening...
                    </div>
                </div>

                <!-- Paragraph Mode Input -->
                <div id="paragraphModeInput" class="hidden">
                    <textarea id="symptomParagraph" 
                            class="w-full h-32 shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                            placeholder="Describe all your symptoms in detail. For example: I've been having severe back pain for the last 10 days. Sometimes it pains heavily, sometimes it doesn't..."></textarea>
                    <div class="flex space-x-2 mt-2">
                        <button id="micButtonParagraph" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path>
                            </svg>
                        </button>
                        <button id="analyzeParagraph" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                            Analyze Paragraph
                        </button>
                    </div>
                    <div id="micStatusParagraph" class="mt-2 text-sm text-gray-600 hidden">
                        Microphone is listening...
                    </div>
                </div>
            </div>

            <div class="mt-6">
                <h3 class="font-semibold mb-3">Your Symptoms:</h3>
                <div id="symptomsList" class="space-y-2"></div>
            </div>

            <div class="mt-6 flex justify-between items-center">
                <button id="analyzeNow" class="hidden bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                    Analyze Symptoms
                </button>
                <p class="text-sm text-gray-600">
                    * Add at least one symptom to continue
                </p>
            </div>
        </div>

        <!-- Analysis Results -->
        <div id="resultsSection" class="hidden">
            <div class="bg-white shadow-lg rounded-lg px-8 pt-6 pb-8 mb-4">
                <h2 class="text-2xl font-semibold mb-6">Analysis Results</h2>
                <div id="analysisResults" class="space-y-6">
                    <!-- Results will be inserted here -->
                </div>
            </div>

            <div class="flex space-x-4 justify-center mt-6">
                <button id="startOver" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                    Start New Analysis
                </button>
                <button id="printResults" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                    Print Results
                </button>
            </div>
        </div>
    </div>

    <script>
        let patientName = '';
        let patientAge = '';
        let patientGender = '';
        let symptoms = [];
        let recognition = null;
        let isListening = false;
        let isParagraphMode = false;

        // Help Modal
        document.getElementById('helpBtn').addEventListener('click', () => {
            document.getElementById('helpModal').classList.remove('hidden');
        });

        document.getElementById('closeHelp').addEventListener('click', () => {
            document.getElementById('helpModal').classList.add('hidden');
        });

        // Progress Steps
        function updateProgress(step) {
            const steps = document.querySelectorAll('.progress-step');
            steps.forEach((s, index) => {
                if (index < step) {
                    s.classList.remove('opacity-50');
                    s.querySelector('div').classList.add('bg-blue-500');
                    s.querySelector('div').classList.remove('bg-gray-300');
                } else if (index === step) {
                    s.classList.remove('opacity-50');
                    s.classList.add('active');
                } else {
                    s.classList.add('opacity-50');
                    s.querySelector('div').classList.add('bg-gray-300');
                    s.querySelector('div').classList.remove('bg-blue-500');
                }
            });
        }

        // Common Symptoms
        document.getElementById('commonSymptoms').addEventListener('click', (e) => {
            if (e.target.classList.contains('symptom-tag')) {
                document.getElementById('symptomInput').value = e.target.textContent;
            }
        });

        // Initialize speech recognition
        function initSpeechRecognition() {
            if ('webkitSpeechRecognition' in window) {
                recognition = new webkitSpeechRecognition();
                recognition.continuous = false;
                recognition.interimResults = false;
                recognition.lang = 'en-US';

                recognition.onstart = function() {
                    isListening = true;
                    const micButton = isParagraphMode ? 
                        document.getElementById('micButtonParagraph') : 
                        document.getElementById('micButton');
                    const micStatus = isParagraphMode ? 
                        document.getElementById('micStatusParagraph') : 
                        document.getElementById('micStatus');
                    
                    micButton.classList.remove('bg-blue-500');
                    micButton.classList.add('bg-red-500');
                    micStatus.classList.remove('hidden');
                };

                recognition.onend = function() {
                    isListening = false;
                    const micButton = isParagraphMode ? 
                        document.getElementById('micButtonParagraph') : 
                        document.getElementById('micButton');
                    const micStatus = isParagraphMode ? 
                        document.getElementById('micStatusParagraph') : 
                        document.getElementById('micStatus');
                    
                    micButton.classList.remove('bg-red-500');
                    micButton.classList.add('bg-blue-500');
                    micStatus.classList.add('hidden');
                };

                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    if (isParagraphMode) {
                        const textarea = document.getElementById('symptomParagraph');
                        textarea.value = textarea.value + (textarea.value ? ' ' : '') + transcript;
                    } else {
                        document.getElementById('symptomInput').value = transcript;
                    }
                };

                recognition.onerror = function(event) {
                    console.error('Speech recognition error:', event.error);
                    isListening = false;
                    const micButton = isParagraphMode ? 
                        document.getElementById('micButtonParagraph') : 
                        document.getElementById('micButton');
                    const micStatus = isParagraphMode ? 
                        document.getElementById('micStatusParagraph') : 
                        document.getElementById('micStatus');
                    
                    micButton.classList.remove('bg-red-500');
                    micButton.classList.add('bg-blue-500');
                    micStatus.classList.add('hidden');
                };
            }
        }

        // Initialize speech recognition when the page loads
        window.addEventListener('load', initSpeechRecognition);

        // Handle microphone button clicks
        document.getElementById('micButton').addEventListener('click', () => {
            isParagraphMode = false;
            handleMicClick();
        });

        document.getElementById('micButtonParagraph').addEventListener('click', () => {
            isParagraphMode = true;
            handleMicClick();
        });

        function handleMicClick() {
            if (!recognition) {
                alert('Speech recognition is not supported in your browser. Please use a modern browser like Chrome.');
                return;
            }

            if (!isListening) {
                recognition.start();
            } else {
                recognition.stop();
            }
        }

        // Handle mode switching
        document.getElementById('listModeBtn').addEventListener('click', () => {
            document.getElementById('listModeInput').classList.remove('hidden');
            document.getElementById('paragraphModeInput').classList.add('hidden');
            document.getElementById('listModeBtn').classList.remove('bg-gray-300', 'text-gray-700');
            document.getElementById('listModeBtn').classList.add('bg-blue-500', 'text-white');
            document.getElementById('paragraphModeBtn').classList.remove('bg-blue-500', 'text-white');
            document.getElementById('paragraphModeBtn').classList.add('bg-gray-300', 'text-gray-700');
            isParagraphMode = false;
        });

        document.getElementById('paragraphModeBtn').addEventListener('click', () => {
            document.getElementById('paragraphModeInput').classList.remove('hidden');
            document.getElementById('listModeInput').classList.add('hidden');
            document.getElementById('paragraphModeBtn').classList.remove('bg-gray-300', 'text-gray-700');
            document.getElementById('paragraphModeBtn').classList.add('bg-blue-500', 'text-white');
            document.getElementById('listModeBtn').classList.remove('bg-blue-500', 'text-white');
            document.getElementById('listModeBtn').classList.add('bg-gray-300', 'text-gray-700');
            isParagraphMode = true;
        });

        // Name Section Handling
        document.getElementById('submitName').addEventListener('click', () => {
            patientName = document.getElementById('patientName').value.trim();
            patientAge = document.getElementById('patientAge').value.trim();
            patientGender = document.querySelector('input[name="gender"]:checked')?.value;

            if (patientName && patientAge && patientGender) {
                document.getElementById('nameSection').classList.add('hidden');
                document.getElementById('symptomsSection').classList.remove('hidden');
                updateProgress(1);
            } else {
                alert('Please fill in all required information');
            }
        });

        // Symptoms Handling
        document.getElementById('addSymptom').addEventListener('click', () => {
            const symptomInput = document.getElementById('symptomInput');
            const symptom = symptomInput.value.trim();
            
            if (symptom && !symptoms.includes(symptom)) {
                if (symptoms.length >= 7) {
                    alert('Maximum number of symptoms reached');
                    return;
                }
                
                symptoms.push(symptom);
                updateSymptomsList();
                symptomInput.value = '';
                
                // Show analyze button after first symptom
                document.getElementById('analyzeNow').classList.remove('hidden');
                
                // Update symptom counter
                document.getElementById('symptomCounter').textContent = symptoms.length + 1;
            }
        });

        function updateSymptomsList() {
            const list = document.getElementById('symptomsList');
            list.innerHTML = symptoms.map((symptom, index) => `
                <div class="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <span>${symptom}</span>
                    <button onclick="removeSymptom(${index})" class="text-red-500 hover:text-red-700">×</button>
                </div>
            `).join('');
        }

        function removeSymptom(index) {
            symptoms.splice(index, 1);
            updateSymptomsList();
            document.getElementById('symptomCounter').textContent = symptoms.length + 1;
            if (symptoms.length === 0) {
                document.getElementById('analyzeNow').classList.add('hidden');
            }
        }

        // Handle paragraph analysis
        document.getElementById('analyzeParagraph').addEventListener('click', async () => {
            const paragraph = document.getElementById('symptomParagraph').value.trim();
            if (!paragraph) {
                alert('Please enter your symptoms description');
                return;
            }

            document.getElementById('loadingOverlay').classList.remove('hidden');
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: patientName,
                        symptoms: [paragraph], // Send the entire paragraph as one symptom
                        age: patientAge,
                        gender: patientGender,
                        mode: 'paragraph'
                    })
                });

                if (!response.ok) throw new Error('Network response was not ok');
                
                const result = await response.json();
                displayAnalysis(result);
            } catch (error) {
                console.error('Error:', error);
                alert('An error occurred while analyzing symptoms. Please try again.');
            } finally {
                document.getElementById('loadingOverlay').classList.add('hidden');
            }
        });

        // Analysis
        document.getElementById('analyzeNow').addEventListener('click', async () => {
            if (symptoms.length === 0) {
                alert('Please add at least one symptom');
                return;
            }

            // Show loading overlay
            document.getElementById('loadingOverlay').classList.remove('hidden');

            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: patientName,
                        symptoms: symptoms
                    })
                });

                const result = await response.json();

                if (response.ok) {
                    displayAnalysis(result);
                } else {
                    alert(result.error || 'Analysis failed');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error during analysis');
            } finally {
                document.getElementById('loadingOverlay').classList.add('hidden');
            }
        });

        function displayAnalysis(result) {
            document.getElementById('symptomsSection').classList.add('hidden');
            document.getElementById('resultsSection').classList.remove('hidden');
            updateProgress(2);

            const resultsDiv = document.getElementById('analysisResults');
            resultsDiv.innerHTML = `
                <div class="space-y-4">
                    <div class="p-4 bg-gray-50 rounded">
                        <p class="font-bold">Patient Information:</p>
                        <p>Name: ${patientName}</p>
                        <p>Age: ${patientAge}</p>
                        <p>Gender: ${patientGender}</p>
                        <p class="mt-2">Symptoms: ${symptoms.join(', ')}</p>
                    </div>

                    <div class="space-y-4">
                        ${result.diseases.map(disease => `
                            <div class="p-4 border rounded-lg">
                                <div class="flex justify-between items-start">
                                    <div>
                                        <h4 class="text-lg font-semibold">${disease.name}</h4>
                                        <p class="text-sm text-gray-500">Confidence: ${disease.confidence}%</p>
                                    </div>
                                </div>
                                <p class="mt-2">${disease.description}</p>
                                <div class="mt-2">
                                    <p class="font-medium">Risk Factors:</p>
                                    <ul class="list-disc ml-5">
                                        ${disease.risk_factors.map(factor => `<li>${factor}</li>`).join('')}
                                    </ul>
                                </div>
                            </div>
                        `).join('')}
                    </div>

                    <div class="p-4 border-l-4 border-green-500 bg-green-50">
                        <p class="font-bold">Recommended Treatments:</p>
                        <ul class="list-disc ml-4 mt-2">
                            ${result.treatments.map(treatment => `
                                <li>${treatment}</li>
                            `).join('')}
                        </ul>
                    </div>

                    <div class="p-4 border-l-4 border-yellow-500 bg-yellow-50">
                        <p class="font-bold">Preventive Measures:</p>
                        <ul class="list-disc ml-4 mt-2">
                            ${result.preventive_measures.map(measure => `
                                <li>${measure}</li>
                            `).join('')}
                        </ul>
                    </div>

                    <div class="p-4 border-l-4 border-blue-500 bg-blue-50">
                        <p class="font-bold">Follow-up Recommendations:</p>
                        <ul class="list-disc ml-4 mt-2">
                            ${result.follow_up.map(recommendation => `
                                <li>${recommendation}</li>
                            `).join('')}
                        </ul>
                    </div>

                    <div class="p-4 border-l-4 border-red-500 bg-red-50">
                        <p class="font-bold">Immediate Actions:</p>
                        <ul class="list-disc ml-4 mt-2">
                            ${result.immediate_actions.map(action => `
                                <li>${action}</li>
                            `).join('')}
                        </ul>
                    </div>

                    ${result.seek_medical_attention ? `
                        <div class="p-4 border-l-4 border-red-500 bg-red-50">
                            <p class="font-bold text-red-700">⚠️ Please seek immediate medical attention!</p>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Print Results
        document.getElementById('printResults').addEventListener('click', () => {
            window.print();
        });

        // Start Over
        document.getElementById('startOver').addEventListener('click', () => {
            location.reload();
        });
    </script>
'''

def analyze_symptoms(name, symptoms, age, gender, mode):
    if not model:
        print("Model is not initialized.")
        return None

    # Remove duplicates and clean symptoms
    unique_symptoms = list(set(symptoms))
    
    # Get current Arduino sensor data
    with arduino_data_lock:
        sensor_data = arduino_data.copy()
    
    # Add sensor data to symptoms description
    vital_signs = f"""
Current Vital Signs from Sensors:
- Heart Rate: {sensor_data['heart_rate']} BPM
- Body Temperature: {sensor_data['temperature']}°C
- Body Moisture Level: {sensor_data['moisture']}%
"""
    
    prompt = f"""As a medical analysis system, analyze these symptoms and sensor data to provide a detailed assessment.

Patient: {name}
Age: {age}
Gender: {gender}

{vital_signs}

Reported Symptoms: {', '.join(unique_symptoms) if mode != 'paragraph' else unique_symptoms[0]}

Based on both the symptoms and vital signs, provide a comprehensive analysis that includes:
1. The top 3 most likely conditions/diseases, ranked by probability
2. For each condition, provide:
   - A confidence percentage (0-100)
   - A detailed description including key distinguishing features
   - Specific risk factors for this patient's age and gender
   - How the measured vital signs support or contradict this diagnosis
3. Specific treatment recommendations
4. Whether immediate medical attention is needed (consider abnormal vital signs)
5. Preventive measures to avoid worsening of symptoms
6. Follow-up recommendations and monitoring guidelines

Return your analysis in this exact format (do not include any other text):

{{
    "diseases": [
        {{
            "name": "Example Disease",
            "confidence": 80,
            "description": "Brief description including how vital signs support diagnosis",
            "risk_factors": ["Age related factor", "Gender related factor"]
        }}
    ],
    "treatments": ["First line treatment", "Secondary treatment"],
    "seek_medical_attention": true,
    "severity_level": 70,
    "preventive_measures": ["First measure", "Second measure"],
    "follow_up": ["First follow up step", "Second follow up step"],
    "immediate_actions": ["First immediate action", "Second immediate action"]
}}"""

    try:
        response = model.generate_content(prompt)
        if not response or not response.text:
            print("Empty response from model")
            return create_default_response()
            
        # Try to find JSON object in the response
        text = response.text.strip()
        try:
            # Find the first { and last } to extract JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                # Clean up any potential formatting issues
                json_str = json_str.replace('\n', ' ').replace('\r', '')
                analysis = json.loads(json_str)
            else:
                print("No JSON object found in response")
                return create_default_response()
            
            # Validate and ensure all required fields
            analysis = validate_and_fix_analysis(analysis)
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return create_default_response()
            
    except Exception as e:
        print(f"Error generating analysis: {e}")
        return create_default_response()

def create_default_response():
    """Create a default response when analysis fails"""
    return {
        "diseases": [
            {
                "name": "Analysis Unavailable",
                "confidence": 0,
                "description": "Unable to analyze symptoms at this time. Please try again or consult a healthcare provider.",
                "risk_factors": ["N/A"]
            }
        ],
        "treatments": ["Please consult a healthcare provider"],
        "seek_medical_attention": True,
        "severity_level": 50,
        "preventive_measures": [
            "Rest and maintain good hydration",
            "Monitor symptoms for any changes",
            "Practice good hygiene"
        ],
        "follow_up": [
            "Schedule an appointment with your healthcare provider",
            "Keep a symptom diary"
        ],
        "immediate_actions": [
            "Contact your healthcare provider",
            "Monitor your symptoms"
        ]
    }

def validate_and_fix_analysis(analysis):
    """Validate and ensure all required fields are present"""
    default_response = create_default_response()
    
    if not isinstance(analysis, dict):
        return default_response
        
    # Ensure all required fields exist
    for key in default_response.keys():
        if key not in analysis:
            analysis[key] = default_response[key]
            
    # Validate diseases array
    if not isinstance(analysis.get('diseases'), list) or not analysis['diseases']:
        analysis['diseases'] = default_response['diseases']
    
    # Ensure each disease has all required fields
    for disease in analysis['diseases']:
        if not isinstance(disease, dict):
            continue
        if 'name' not in disease:
            disease['name'] = "Unknown Condition"
        if 'confidence' not in disease:
            disease['confidence'] = 0
        if 'description' not in disease:
            disease['description'] = "No description available"
        if 'risk_factors' not in disease or not isinstance(disease['risk_factors'], list):
            disease['risk_factors'] = ["No risk factors specified"]
            
    return analysis

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        name = data.get('name', '')
        symptoms = data.get('symptoms', [])
        age = data.get('age', '')
        gender = data.get('gender', '')
        mode = data.get('mode', '')
        
        if not name or not symptoms:
            return jsonify({'error': 'Invalid input'}), 400
        
        if len(symptoms) > 7:
            return jsonify({'error': 'Maximum 7 symptoms allowed'}), 400
        
        # Add artificial delay to show loading screen (remove in production)
        time.sleep(2)
        
        analysis_result = analyze_symptoms(name, symptoms, age, gender, mode)
        if analysis_result:
            return jsonify(analysis_result)
        return jsonify({'error': 'Analysis failed'}), 500

    except Exception as e:
        print(f"Error in analyze route: {str(e)}")
        return jsonify({'error': 'Server error occurred'}), 500

@app.route('/sensor_data')
def get_sensor_data():
    """API endpoint to get current sensor data"""
    with arduino_data_lock:
        return jsonify(arduino_data)

if __name__ == '__main__':
    # Allow external access on Raspberry Pi
    app.run(host='0.0.0.0', port=5000, debug=True)