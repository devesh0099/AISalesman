# import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import requests
import time
import os
from dotenv import load_dotenv
from threading import Thread, Event
from queue import Queue, Empty

load_dotenv()

HUGGINGFACE_API_TOKEN = os.environ.get("HUGGING_FACE_API")
API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}

sample_rate = 16000
duration = 5
stop_recording = Event()
audio_queue = Queue()
transcriptions = []

def detect_silence(audio_data, threshold=0.005):
    rms = np.sqrt(np.mean(np.square(audio_data)))
    return rms < threshold

# def record_audio_continuous():
#     print("Recording started. Speak now (or press Enter to stop)...")
#     try:
#         while not stop_recording.is_set():
#             start_time = time.time()
            
#             # Record audio
#             audio = sd.rec(int(sample_rate * duration), samplerate=sample_rate, channels=1, dtype='float32')
#             sd.wait()
#             audio = audio.flatten()
            
#             end_time = time.time()
            
#             # Only add to queue if not silent
#             if not detect_silence(audio):
#                 audio_queue.put(audio)
#                 print(f"\nRecorded segment: {end_time - start_time:.2f}s")
            
#     except Exception as e:
#         print(f"Recording error: {str(e)}")
#         stop_recording.set()

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

def process_audio_queue():
    """Process audio segments from the queue and transcribe them."""
    while not stop_recording.is_set() or not audio_queue.empty():
        try:
            # Wait for 1 second for new audio data
            try:
                audio_data = audio_queue.get(timeout=1)
            except Empty:  # Changed from Queue.Empty to Empty
                continue
                
            transcription = transcribe_audio(audio_data)
            if transcription:
                transcriptions.append(transcription)
                print(f"Transcription: {transcription}")
                
        except Exception as e:
            print(f"Processing error: {str(e)}")
            time.sleep(0.1)  # Add small delay to prevent tight loop



# def main():
#     try:
#         # Start recording thread
#         recording_thread = Thread(target=record_audio_continuous)
#         recording_thread.start()
        
#         # Start processing thread
#         processing_thread = Thread(target=process_audio_queue)
#         processing_thread.start()
        
#         input("Press Enter to stop recording...\n")
        
#         # Signal threads to stop
#         stop_recording.set()
        
#         # Wait for threads to finish
#         recording_thread.join()
#         processing_thread.join()
        
#         # Print final transcription
#         if transcriptions:
#             print("\nComplete transcription:")
#             completed_transcription = " ".join(transcriptions)
#             return completed_transcription
#             # model.main(completed_transcription)
#             # print(" ".join(transcriptions))
#         else:
#             print("\nNo transcriptions were generated.")
#             return "\nNo transcriptions were generated."
        
#     except KeyboardInterrupt:
#         print("\nStopping recording...")
#         stop_recording.set()
#     except Exception as e:
#         print(f"Main error: {str(e)}")
#         stop_recording.set()
#     finally:
#         stop_recording.set()

# if __name__ == "__main__":
#     main()