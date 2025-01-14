import os
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import FileResponse
from gtts import gTTS

app = FastAPI()

# Dummy Speech-to-Text model (replace with your actual model)
def speech_to_text_model(audio_data: np.ndarray):
    # Here you would process the audio chunk and return a transcription
    return {"text": "Example transcription"}  # Placeholder

@app.websocket("/ws/speech-to-text/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    transcription = ""  # Collect transcription data here
    
    try:
        while True:
            # Receive the incoming audio chunk (in bytes)
            audio_chunk = await websocket.receive_bytes()
            
            # Convert the byte data into the appropriate format for your speech-to-text model
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)  # Adjust based on your audio format
            
            # Send the audio chunk to the speech-to-text model for transcription
            transcription_chunk = speech_to_text_model(audio_data)
            transcription += transcription_chunk["text"]  # Append the new transcription
            
            # Send the transcription back to the client (can be processed further on client side)
            await websocket.send_json({"transcription": transcription})

    except WebSocketDisconnect:
        print("Client disconnected")

    except Exception as e:
        print(f"Error occurred: {e}")
        await websocket.close(code=1000)  # Close the connection if an error occurs


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
