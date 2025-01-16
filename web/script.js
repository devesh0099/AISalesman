let calls = [];
let currentSection = 'botSelector';

let mediaRecorder = null;
let recordingInterval = null;
let audioChunks = [];
let socket = null;
let conversationSocket = null;
const CHUNK_DURATION = 5000; // 5 seconds in milliseconds

const sections = {
    botSelector: document.getElementById('botSelector'),
    salesBot: document.getElementById('salesBot'),
    callManager: document.getElementById('callManager'),
};

const resetButton = document.getElementById('resetButton');
const startSalesCallButton = document.getElementById('startSalesCall');
const addSalesCallButton = document.getElementById('addSalesCall');
const activeCalls = document.getElementById('activeCalls');

function showSection(sectionId) {
    if (currentSection && currentSection !== sectionId) {
        sections[currentSection].classList.add('completed');
    }
    
    sections[sectionId].classList.add('active');
    
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
    const endCallButton = callContainer.querySelector('.end-call');

    let isListening = false;

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

        mediaRecorder.ondataavailable = async (event) => {
            const audioBlob = event.data;
            if (audioBlob.size > 0) {
                try {
                    const arrayBuffer = await audioBlob.arrayBuffer();
                    const audioContext = new AudioContext({ sampleRate: 16000 }); // Set sample rate to 16 kHz
                    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

                    const float32Array = audioBuffer.numberOfChannels > 1
                        ? audioBuffer.getChannelData(0) 
                        : audioBuffer.getChannelData(0);

                    const normalizedArray = float32Array.map(sample =>
                        Math.max(-1.0, Math.min(1.0, sample))
                    );

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
            conversationSocket.send(JSON.stringify({
                type: "transcript",
                text: "Hello, who is this?"
            }));
        };
        
        conversationSocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
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
            console.log(data.path)
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
        window.location.reload();
    });

    calls.push({ id: callId, type: callType, scenario });
    return callContainer;
}

resetButton.addEventListener('click', () => {
    window.location.reload();
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

// Initialize the app
showSection('botSelector');