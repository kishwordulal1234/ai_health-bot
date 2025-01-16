from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai
import json
import time

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
                <p class="text-gray-600 mb-2">Symptom <span id="symptomCounter">1</span> of 7:</p>
                <div class="flex space-x-2">
                    <input class="flex-1 shadow appearance-none border rounded py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
                           id="symptomInput" type="text" placeholder="Type or select a symptom">
                    <button id="addSymptom" class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full focus:outline-none focus:shadow-outline transform transition hover:scale-105">
                        Add
                    </button>
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
        const MAX_SYMPTOMS = 7;

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
                if (symptoms.length >= MAX_SYMPTOMS) {
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
                    displayResults(result);
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

        function displayResults(result) {
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
                            <div class="p-4 border-l-4 border-blue-500 bg-blue-50">
                                <p class="font-bold">${disease.name}</p>
                                <div class="w-full bg-gray-200 rounded-full h-2.5 my-2">
                                    <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${disease.confidence}%"></div>
                                </div>
                                <p>Confidence: ${disease.confidence}%</p>
                                <p class="mt-2">${disease.description}</p>
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

def analyze_symptoms(name, symptoms):
    if not model:
        print("Model is not initialized.")
        return None

    # Remove duplicates and clean symptoms
    unique_symptoms = list(set(symptoms))
    
    prompt = f"""As a medical analysis system, analyze these symptoms and provide a detailed assessment.

Patient: {name}
Symptoms: {', '.join(unique_symptoms)}

Based on these symptoms, provide a comprehensive analysis that includes:
1. The top 3 most likely conditions/diseases, ranked by probability
2. For each condition, provide:
   - A confidence percentage (0-100)
   - A detailed description including key distinguishing features
3. Specific treatment recommendations
4. Whether immediate medical attention is needed

Return your analysis ONLY as a JSON object with this exact structure:
{{
    "diseases": [
        {{
            "name": string,
            "confidence": number,
            "description": string
        }}
    ],
    "treatments": [string],
    "seek_medical_attention": boolean
}}

Consider current medical knowledge and all possible conditions including COVID-19, seasonal illnesses, and other relevant diseases."""

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON if there's surrounding text
        try:
            start_idx = response_text.index('{')
            end_idx = response_text.rindex('}') + 1
            json_str = response_text[start_idx:end_idx]
        except ValueError:
            json_str = response_text

        result = json.loads(json_str)
        return result

    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        return None

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        name = data.get('name', '')
        symptoms = data.get('symptoms', [])
        
        if not name or not symptoms:
            return jsonify({'error': 'Invalid input'}), 400
        
        if len(symptoms) > 7:
            return jsonify({'error': 'Maximum 7 symptoms allowed'}), 400
        
        # Add artificial delay to show loading screen (remove in production)
        time.sleep(2)
        
        analysis_result = analyze_symptoms(name, symptoms)
        if analysis_result:
            return jsonify(analysis_result)
        return jsonify({'error': 'Analysis failed'}), 500

    except Exception as e:
        print(f"Error in analyze route: {str(e)}")
        return jsonify({'error': 'Server error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)