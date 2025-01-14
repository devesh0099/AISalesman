import os
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
import base64
from typing import List
import time
from liveTranscription import transcribe_audio

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
# app.mount("/", StaticFiles(directory="web", html=True), name="static")

# Store complete transcripts for each session
session_transcripts: dict = {}

# @app.websocket("/ws/speech-to-text/")
# async def websocket_endpoint(websocket: WebSocket):
#     # print("Done here called")
#     await websocket.accept()
#     session_id = str(time.time())  # Create unique session ID
#     session_transcripts[session_id] = []
    
#     try:
#         while True:
#             # Receive audio chunk
#             audio_data = await websocket.receive_bytes()
            
#             # Convert audio bytes to numpy array
#             audio_array = np.frombuffer(audio_data, dtype=np.float32)
            
            
#             # Get transcription for this chunk
            
#             transcript_chunk = transcribe_audio(audio_array)
            

#             if transcript_chunk:
#                 # Add to session transcript
#                 session_transcripts[session_id].append(transcript_chunk)
                
#                 # Send back current transcription
                
#                 await websocket.send_json({
#                     "transcription": transcript_chunk,
#                     "complete_transcript": " ".join(session_transcripts[session_id])
#                 })

#     except WebSocketDisconnect:
#         print(f"Client disconnected, session {session_id}")
#         # Clean up session data
#         if session_id in session_transcripts:
#             complete_transcript = " ".join(session_transcripts[session_id])
#             del session_transcripts[session_id]
#             return complete_transcript

#     except Exception as e:
#         print(f"Error occurred: {e}")
#         await websocket.close(code=1000)
#         if session_id in session_transcripts:
#             del session_transcripts[session_id]
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


# @app.websocket("/ws/speech-to-text/")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     session_transcripts = []

#     try:
#         while True:
#             # Receive audio data
#             audio_data = await websocket.receive_bytes()

#             # Convert to NumPy array
#             audio_array = np.frombuffer(audio_data, dtype=np.float32)

#             # Process and transcribe
#             if len(audio_array) > 0:
#                 transcription = transcribe_audio(audio_array)
#                 if transcription:
#                     session_transcripts.append(transcription)
#                     await websocket.send_json({
#                         "transcription": transcription,
#                         "complete_transcript": " ".join(session_transcripts)
#                     })
#     except WebSocketDisconnect:
#         print("Client disconnected")


@app.post("/generate-response/")
async def generate_response(input_text: str = Form(...)):
    # Assuming you are using some model to generate the response text
    response = response_generator_model(input_text, max_length=150, num_return_sequences=1)
    return {"response": response[0]["generated_text"]}


@app.post("/text-to-speech/")
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
