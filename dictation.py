import pyaudio
import whisper
import pyautogui
import keyboard
import threading
import queue
import time
import numpy as np
import logging
import simpleaudio as sa  # Cross-platform sound playback

# Initialize Whisper model
model = whisper.load_model("small")

# Queue for audio frames
audio_queue = queue.Queue()

# Setup logging
logging.basicConfig(filename='recording_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# Function to list and select an audio input device
def select_audio_input_device():
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    print("Available audio input devices:")
    for i in range(device_count):
        device_info = p.get_device_info_by_index(i)
        if device_info['maxInputChannels'] > 0:
            print(f"{i}: {device_info['name']}")
    
    device_index = int(input("Select the device index for audio input (default is 6): ") or 6)
    p.terminate()
    return device_index

# Function to record audio from selected input device
def record_audio(device_index):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, input_device_index=device_index, frames_per_buffer=512)

    while recording:
        data = stream.read(4096)
        audio_queue.put(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

# Function to process audio and do real-time dictation
def process_audio():
    audio_frames = []
    while not audio_queue.empty():
        data = audio_queue.get()
        audio_frames.append(data)

    if audio_frames:
        audio_data = np.frombuffer(b''.join(audio_frames), dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32768.0
        text = model.transcribe(audio_data)["text"]

        # Filter out unwanted phrases
        filtered_text = text.replace("Thank you.", "").strip()

        # Additional filters for whitespace or specific unwanted text
        if filtered_text and filtered_text != "you" and filtered_text.strip():
            pyautogui.write(filtered_text)
        time.sleep(0.5)

# Function to generate and play a single beep sound
def play_beep(frequency=440, duration=0.1):
    fs = 44100  # Sampling rate
    t = np.linspace(0, duration, int(fs * duration), False)
    wave = np.sin(frequency * t * 2 * np.pi)
    audio = wave * (2**15 - 1) / np.max(np.abs(wave))
    audio = audio.astype(np.int16)
    play_obj = sa.play_buffer(audio, 1, 2, fs)
    play_obj.wait_done()

# Function to toggle recording
def toggle_recording():
    global recording
    if recording:
        recording = False  # Stop recording
        print("Recording stopped.")
        logging.info("Recording stopped.")
        play_beep()  # Play beep sound on stop
        process_audio()  # Process audio after recording stops
    else:
        recording = True  # Start recording
        print("Recording started...")
        logging.info("Recording started.")
        play_beep()  # Play beep sound on start
        threading.Thread(target=record_audio, args=(selected_device_index,)).start()

# Select audio input device
selected_device_index = select_audio_input_device()

# Setup hotkey
recording = False
keyboard.add_hotkey('ctrl+alt+space', toggle_recording)

print("Press ctrl+alt+space to start/stop recording and process dictation.")
keyboard.wait('esc')  # Press 'Esc' to exit the script
