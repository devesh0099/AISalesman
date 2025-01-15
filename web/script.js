// Global variables
let calls = [];
let currentSection = 'botSelector';

let mediaRecorder = null;
let recordingInterval = null;
let audioChunks = [];
let socket = null;
let conversationSocket = null;
const CHUNK_DURATION = 5000; // 5 seconds in milliseconds

// DOM elements
const sections = {
    botSelector: document.getElementById('botSelector'),
    salesBot: document.getElementById('salesBot'),
    leadBot: document.getElementById('leadBot'),
    callManager: document.getElementById('callManager'),
    callSummary: document.getElementById('callSummary')
};

const resetButton = document.getElementById('resetButton');
const startSalesCallButton = document.getElementById('startSalesCall');
const addSalesCallButton = document.getElementById('addSalesCall');
const addLeadCallButton = document.getElementById('addLeadCall');
const leadOptions = document.getElementById('leadOptions');
const activeCalls = document.getElementById('activeCalls');
const customScenarioForm = document.getElementById('customScenarioForm');

// Lead scenarios
const leadScenarios = [
    { title: "Discussing Discounts", person: "John Doe", description: "Follow up with a potential customer who has shown interest but is concerned about pricing." },
    { title: "Past Customer Follow-up", person: "Jane Smith", description: "Reach out to a former student to discuss new course offerings and potential return enrollment." },
    { title: "Missed Session", person: "Mike Johnson", description: "Contact a student who missed a scheduled session to reschedule and ensure continued engagement." },
    { title: "Course Enquiry", person: "Emily Brown", description: "Respond to a new lead who has requested information about specific courses and programs." },
    { title: "Fee Structure", person: "David Wilson", description: "Explain the fee structure and payment options to a potential student who has expressed interest." }
];

// Helper functions
function showSection(sectionId) {
    // Mark previous section as completed
    if (currentSection && currentSection !== sectionId) {
        sections[currentSection].classList.add('completed');
    }
    
    // Show new section
    sections[sectionId].classList.add('active');
    
    // Scroll new section into view
    sections[sectionId].scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    currentSection = sectionId;
}

function createCallInterface(callType, scenario) {
    const callId = Date.now().toString();
    const callContainer = document.createElement('div');
    callContainer.className = 'call-container';
    callContainer.innerHTML = `
        <div class="call-interface">
            <h3>${callType === 'sales' ? 'Sales Call' : `Lead Call: ${scenario || 'Custom'}`}</h3>
            <div class="voice-circle user">Start The Call</div>
            <div class="transcript">
                <h4>Transcript:</h4>
                <p></p>
            </div>
            <div class="ai-response" style="display: none;">
                <h4>AI Response:</h4>
                <p></p>
            </div>
            <button class="end-call">End Call</button>
        </div>
    `;

    const voiceCircle = callContainer.querySelector('.voice-circle');
    const transcript = callContainer.querySelector('.transcript p');
    const aiResponse = callContainer.querySelector('.ai-response');
    const aiResponseText = callContainer.querySelector('.ai-response p');
    const endCallButton = callContainer.querySelector('.end-call');

    let isListening = false;
    let recognition;

    function startRecording() {
        navigator.mediaDevices.getUserMedia({ 
            audio: { 
                sampleRate: 16000,  // Match the sample rate with backend
                channelCount: 1     // Mono audio
            } 
        })
        .then((stream) => {
            mediaRecorder = new MediaRecorder(stream);
            socket = new WebSocket(`${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/speech-to-text/`);
            
            // Set up WebSocket handlers
            socket.onopen = () => {
                console.log("Transcription connection established");
                startAudioChunking();
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleTranscription(data);
            };

            socket.onerror = (error) => {
                console.error("Transcription error:", error);
            };

            socket.onclose = () => {
                console.log("Transcription connection closed");
                stopRecording();
            };

            // Start recording
            mediaRecorder.start();
        })
        .catch((error) => {
            console.error("Error accessing microphone:", error);
        });
    }

    function startAudioChunking() {
        recordingInterval = setInterval(() => {
            if (mediaRecorder && mediaRecorder.state === "recording") {
                mediaRecorder.stop();
                mediaRecorder.start();
            }
        }, CHUNK_DURATION);

        // Handle audio chunks
        mediaRecorder.ondataavailable = async (event) => {
            const audioBlob = event.data;
            if (audioBlob.size > 0) {
                try {
                    const arrayBuffer = await audioBlob.arrayBuffer();
                    const audioContext = new AudioContext({ sampleRate: 16000 }); // Set sample rate to 16 kHz
                    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

                    // Ensure mono channel and normalize to [-1.0, 1.0]
                    const float32Array = audioBuffer.numberOfChannels > 1
                        ? audioBuffer.getChannelData(0) // Use the first channel if stereo
                        : audioBuffer.getChannelData(0);

                    const normalizedArray = float32Array.map(sample =>
                        Math.max(-1.0, Math.min(1.0, sample))
                    );

                    // Send audio data to the backend
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        socket.send(new Float32Array(normalizedArray).buffer);
                    }
                    audioContext.close();
                } catch (error) {
                    console.error("Error processing audio:", error);
                }
            }
        };
    }

    function stopRecording() {
        
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }

        if (mediaRecorder) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            mediaRecorder = null;
        }

        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }

        if (recordingInterval) {
            clearInterval(recordingInterval);
            recordingInterval = null;
        }
    }

    function handleTranscription(data) {
        const transcriptElement = document.querySelector('.transcript p');
        if (transcriptElement) {
            transcriptElement.textContent = data.complete_transcript;
        }
    }
    
    function initializeConversation() {
        const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/generate-response/`;
        conversationSocket = new WebSocket(wsUrl);
        
        conversationSocket.onopen = () => {
            console.log("LLM WebSocket connected");
        };
        
        conversationSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // console.log(event)
            handleAIResponse(data);
        };
        
        conversationSocket.onerror = (error) => {
            console.error("LLM WebSocket error:", error);
        };
        
        conversationSocket.onclose = () => {
            console.log("LLM ended");
            conversationSocket = null;
        };
    }

    function handleAIResponse(data) {
        const aiResponseElement = document.querySelector('.ai-response p');
        const voiceCircle = document.querySelector('.voice-circle');
        if (data.response) {
            let audio = new Audio(data.audio)
            audio.play()
            const responseText = typeof data.response === 'object' ? 
            data.response.text || data.response.toString() : 
            data.response;

            aiResponseElement.textContent = responseText;
            document.querySelector('.ai-response').style.display = 'block';
            voiceCircle.textContent = 'Tap to Speak';
            voiceCircle.classList.remove('ai');
        }
        if(data.path) {
            print(data)
            print(data.path)
            let audio = new Audio(data.path);
            audio.play();
            voiceCircle.textContent = 'Tap to Speak';
            voiceCircle.classList.remove('ai');
        }
        
        voiceCircle.textContent = 'Tap to Speak';
        voiceCircle.classList.remove('ai');
    }

    voiceCircle.addEventListener('click', () => {
        if (!isListening) {
            if (!conversationSocket) {
                initializeConversation();
                setTimeout(function(){
                    conversationSocket.send(JSON.stringify({
                        type:"transcript",
                        text:"Hello, who is this?"
                    }));
                }, 1000);
            voiceCircle.textContent = 'Processing...';
            return;
            }
            startRecording();
            isListening = true;
            voiceCircle.textContent = 'Speaking...';
            voiceCircle.classList.add('active');
        } else {
            stopRecording();
            isListening = false;
            voiceCircle.textContent = 'AI is responding...';
            voiceCircle.classList.remove('active');
            
            const transcriptText = document.querySelector('.transcript p').textContent;
            if (conversationSocket && conversationSocket.readyState === WebSocket.OPEN) {
                conversationSocket.send(JSON.stringify({
                    type: "transcript",
                    text: transcriptText
                }));
            }
        }
    });

    endCallButton.addEventListener('click', () => {
        calls = calls.filter(call => call.id !== callId);
        callContainer.remove();
        if (calls.length === 0) {
            showSection('callSummary');
            document.getElementById('summaryContent').textContent = "This is a placeholder for the call summary. In a real implementation, this would be generated by the AI based on the conversation.";
        }
    });

    calls.push({ id: callId, type: callType, scenario });
    return callContainer;
}

// Event listeners
resetButton.addEventListener('click', () => {
    // Clear all calls
    calls = [];
    activeCalls.innerHTML = '';
    
    // Reset lead options and custom scenario form
    leadOptions.style.display = 'none';
    customScenarioForm.style.display = 'none';
    customScenarioForm.reset();
    
    // Remove completed and active states from all sections
    Object.values(sections).forEach(section => {
        section.classList.remove('completed', 'active');
    });
    
    // Re-enable bot selection buttons
    document.querySelectorAll('.bot-option').forEach(btn => {
        btn.disabled = false;
    });
    
    // Clear any existing transcripts and AI responses
    document.querySelectorAll('.transcript p').forEach(p => {
        p.textContent = '';
    });
    document.querySelectorAll('.ai-response').forEach(response => {
        response.style.display = 'none';
    });
    
    // Reset current section tracking
    currentSection = 'botSelector';
    
    // Show initial section
    sections.botSelector.classList.add('active');
    
    // Clear summary content
    document.getElementById('summaryContent').textContent = '';
    
    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

document.querySelectorAll('.bot-option').forEach(button => {
    button.addEventListener('click', () => {
        const botType = button.getAttribute('data-bot-type');
        // Grey out bot selector and show next section
        showSection(botType + 'Bot');
        
        // Disable bot selection after choice is made
        document.querySelectorAll('.bot-option').forEach(btn => {
            btn.disabled = true;
        });
    });
});

startSalesCallButton.addEventListener('click', () => {
    const callInterface = createCallInterface('sales');
    activeCalls.appendChild(callInterface);
    showSection('callManager');
});

addSalesCallButton.addEventListener('click', () => {
    const callInterface = createCallInterface('sales');
    activeCalls.appendChild(callInterface);
});

addLeadCallButton.addEventListener('click', () => {
    leadOptions.innerHTML = '';
    leadScenarios.forEach((scenario, index) => {
        const button = document.createElement('button');
        button.textContent = scenario.title;
        button.addEventListener('click', () => {
            const callInterface = createCallInterface('lead', scenario.title);
            activeCalls.appendChild(callInterface);
            leadOptions.style.display = 'none';
        });
        leadOptions.appendChild(button);
    });

    const customButton = document.createElement('button');
    customButton.textContent = 'Custom';
    customButton.addEventListener('click', () => {
        customScenarioForm.style.display = 'flex';
        leadOptions.style.display = 'none';
    });
    leadOptions.appendChild(customButton);

    leadOptions.style.display = 'flex';
});

customScenarioForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const customScenario = document.getElementById('customReason').value;
    const callInterface = createCallInterface('lead', customScenario);
    activeCalls.appendChild(callInterface);
    customScenarioForm.reset();
    customScenarioForm.style.display = 'none';
    showSection('callManager');
});

// Initialize lead scenarios
function initializeScenarioCards() {
    const scenarioCardsContainer = document.querySelector('.scenario-cards');
    leadScenarios.forEach((scenario, index) => {
        const card = document.createElement('div');
        card.className = 'scenario-card';
        card.innerHTML = `
            <h3>${scenario.title}</h3>
            <p><strong>Sample Person:</strong> ${scenario.person}</p>
            <p>${scenario.description}</p>
            <p><strong>Phone:</strong> 555-${Math.floor(100 + Math.random() * 900)}-${Math.floor(1000 + Math.random() * 9000).toString().slice(0, 2)}XX</p>
        `;
        card.addEventListener('click', () => {
            const callInterface = createCallInterface('lead', scenario.title);
            activeCalls.appendChild(callInterface);
            showSection('callManager');
        });
        scenarioCardsContainer.appendChild(card);
    });
}

// Initialize the app
showSection('botSelector');