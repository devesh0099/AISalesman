import numpy as np
from scipy.io.wavfile import write
import requests
import time
import os
from dotenv import load_dotenv
# from threading import Thread, Event
# from queue import Queue, Empty

load_dotenv()

HUGGINGFACE_API_TOKEN = os.environ.get("HUGGING_FACE_API")
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

sample_rate = 16000
duration = 5
# stop_recording = Event()
# audio_queue = Queue()
transcriptions = []

def detect_silence(audio_data, threshold=0.005):
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms < threshold


def transcribe_audio(audio):
    """Transcribe audio data using Hugging Face API."""
    audio_file_path = f"temp_audio_{time.time()}.wav"
    
    try:
        # Write audio file
        write(audio_file_path, sample_rate, (audio * 32767).astype(np.int16))
        
        # Send to API
        with open(audio_file_path, "rb") as audio_file:
            start_api = time.time()
            response = requests.post(API_URL, headers=headers, data=audio_file)
            
            if response.status_code != 200:
                print(f"API Error: Status code {response.status_code}")
                return ""
                
            result = response.json()
            if isinstance(result, dict) and "text" in result:
                transcription = result["text"].strip()
                end_api = time.time()
                if transcription:
                    print(f"Transcribed in {end_api - start_api:.2f}s")
                return transcription
            return ""
            
    except requests.exceptions.RequestException as e:
        print(f"API request error: {str(e)}")
        return ""
    except Exception as e:
        print(f"Transcription error: {str(e)}")
        return ""
    finally:
        if os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
            except Exception:
                pass

