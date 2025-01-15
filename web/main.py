import os
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from typing import Dict
import time
from liveTranscription import transcribe_audio
import model
import json
import tts_file
import toml

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store complete transcripts for each session
session_transcripts: Dict = {}

#Multiple Calls conversation state
conversation_states = {}

conversation_name = {}

@app.websocket("/ws/speech-to-text/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    session_id = str(time.time())
    session_transcripts[session_id] = []

    try:
        while True:
            # Receive audio data
            audio_data = await websocket.receive_bytes()

            # Convert bytes to numpy array (float32)
            audio_array = np.frombuffer(audio_data, dtype=np.float32)

            # Validate audio data range
            if audio_array.max() > 1.0 or audio_array.min() < -1.0:
                raise ValueError("Received audio data is out of range [-1.0, 1.0]")

            print("Data received")

            # Ensure audio data is valid
            if len(audio_array) > 0:
                # Get transcription for this chunk
                print("Given to transcribe")
                transcript_chunk = transcribe_audio(audio_array)
                print("Transcription done")

                if transcript_chunk:
                    # Add to session transcript
                    session_transcripts[session_id].append(transcript_chunk)

                    # Send back current transcription
                    print("Transcription sent back")
                    await websocket.send_json({
                        "transcription": transcript_chunk,
                        "complete_transcript": " ".join(session_transcripts[session_id])
                    })

    except WebSocketDisconnect:
        if session_id in session_transcripts:
            del session_transcripts[session_id]
    except Exception as e:
        if session_id in session_transcripts:
            del session_transcripts[session_id]
        await websocket.close

def send_fake_audio(name):
    dictionary = {}
    audio_path = ""
    dirname = os.path.dirname(__file__)
    dir = os.path.dirname(dirname)
    filename = os.path.join(dir, 'data/vocals/matching.json')
    # print(filename)

    with open(filename, 'r') as file:
        dictionary = json.load(file)
    match(name):
        case "Komal":
            audio_path = dictionary["Komal"]["greeting"]
            return audio_path
        case "Rajeev":
            audio_path = dictionary["Rajeev"]["greeting"]
            return audio_path
        case "Sanjana":
            audio_path = dictionary["Sanjana"]["greeting"]
            return audio_path
        case "Srishti":
            audio_path = dictionary["Srishti"]["greeting"]
            return audio_path
        case "Vansh":
            audio_path = dictionary["Vansh"]["greeting"]
            return audio_path
        case "Vanshika":
            audio_path = dictionary["Vanshika"]["greeting"]
            return audio_path

def generate_unique_paths(response, name):
    timestamp = int(time.time())
    unique_id = f"{timestamp}_{name}_{hash(response)}"
    wav_path = f"/gen/{unique_id}.wav"
    config_path = f"/gen/config_{unique_id}.toml"
    return wav_path, config_path

def tts_file_func(response, name):
    dirname = os.path.dirname(__file__)
    dir = os.path.dirname(dirname)
    wav_path, config_path = generate_unique_paths(response, name)
    
    matching_path = os.path.join(dir, 'data/vocals/matching.json')
    with open(matching_path, "r") as file:
        matching = json.load(file)

    # Generate new config
    config = {
        "model": "F5-TTS",
        "gen_text": response,
        "gen_file": "",
        "remove_silence": False,
        "output_dir": os.path.join(dir, "gen"),
        "output_file": os.path.basename(wav_path)
    }

    match(name):
        case "Komal":
            config["ref_audio"] = matching["Komal"]["voice"]
            config["ref_text"] = matching["Komal"]["text"]
        case "Rajeev":
            config["ref_audio"] = dir + matching["Rajeev"]["voice"]
            config["ref_text"] = matching["Rajeev"]["text"]
        case "Sanjana":
            config["ref_audio"] = dir + matching["Sanjana"]["voice"]
            config["ref_text"] = matching["Sanjana"]["text"]
        case "Srishti":
            config["ref_audio"] = dir + matching["Srishti"]["voice"]
            config["ref_text"] = matching["Srishti"]["text"]
        case "Vansh":
            config["ref_audio"] = dir + matching["Vansh"]["voice"]
            config["ref_text"] = matching["Vansh"]["text"]
        case "Vanshika":
            config["ref_audio"] = dir + matching["Vanshika"]["voice"]
            config["ref_text"] = matching["Vanshika"]["text"]
            
    with open(os.path.join(dir, config_path), "w") as file:
        toml.dump(config, file)
    tts_file.main()
    return wav_path

@app.websocket("/ws/generate-response/")
async def generate_response(websocket: WebSocket):
    await websocket.accept()
    conversation_id = str(time.time())
    response:str = ""
    state = None
    try:
        while True:
            transcriptText = await websocket.receive_text()
            obj = json.loads(transcriptText)
            print(obj['text'])
            state = conversation_states.get(conversation_id)
            if not state:
                print("new user")
                conversation_states[conversation_id] = model.ConversationState()
                state = conversation_states.get(conversation_id)
                # First message - initialize conversation
                # state = model.main(conversation_id)
                # response = str(model.main(conversation_id, transcriptText))    
                # Subsequent messages - use existing state
                name = state.fake_greeting()
                path = send_fake_audio(name)
                conversation_name[conversation_id] = name
                await websocket.send_json(
                    {
                        "path":path,
                        "type":"path"
                    }
                );
            else:
                name = conversation_name.get(conversation_id)
                response = str(state.structure_forming(obj['text']))
                audio = tts_file_func(response,name)
                await websocket.send_json(
                    {
                        "response":response,
                        "audio":audio,
                        "type":"response"
                    }
                );
    
    except WebSocketDisconnect:
        print("LLM Disconnect ")
        # model.cleanup_conversation(conversation_id)
    except Exception as e:
        print(f"Error in conversation: {e}")
        # model.cleanup_conversation(conversation_id)
        await websocket.close()


@app.post("/ws/text-to-speech/")
async def text_to_speech(response_text: str = Form(...)):
    tts = gTTS(response_text)
    output_file = os.path.join("text_to_speech_folder", "response.mp3")
    tts.save(output_file)
    return FileResponse(output_file, media_type="audio/mpeg", filename="response.mp3")

@app.get("/")
async def read_root():
    return FileResponse('web/index.html')

# Mount static files for other assets

app.mount("/static", StaticFiles(directory="web"), name="static")
app.mount("/vocals", StaticFiles(directory="data/vocals"), name="vocals")
app.mount("/gen",StaticFiles(directory="gen"), name="gen")