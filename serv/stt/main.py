import os
import json
import wave
import io
import argparse
import threading
from time import perf_counter as timer
from flask import Flask, request, jsonify
from vosk import Model, KaldiRecognizer

import dotenv

dotenv.load_dotenv()

# --- CLI Setup ---
parser = argparse.ArgumentParser(description="Expedition-0 STT Microservice")
parser.add_argument("--model", type=str, default=os.getenv('STT_MODEL_PATH'), help="Path to Vosk model")
parser.add_argument("--port", type=int, default=5001, help="Port to run the service on")
args = parser.parse_args()

app = Flask(__name__)

# --- Background Loading ---
_model = None
_ready = False


def load_model():
    global _model, _ready
    print(f"Loading model: {args.model}...")
    t_start = timer()
    try:
        _model = Model(args.model, lang='ru')
        _ready = True
        print("System ready. STT initialized.")
        print(f"STT initialization succeeded in {timer() - t_start} s")
    except Exception as e:
        print(f"Failed to load model: {e}")
        print(f"STT initialization failed in {timer() - t_start} s")



@app.route("/recognize", methods=["POST"])
def recognize():
    if not _ready:
        return jsonify({"error": "System heating up. Try again later."}), 418
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    audio_file = request.files["file"]
    # Read the file from the HTTP request directly into RAM
    audio_data = audio_file.read()

    try:
        t_start = timer()

        # Wrap the bytes in BytesIO so the wave module can parse the headers properly
        with wave.open(io.BytesIO(audio_data), "rb") as wf:
            # Optional but recommended: Check if it's Mono 16-bit
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                return jsonify({"error": "Audio must be mono and 16-bit"}), 400

            framerate = wf.getframerate()
            duration = (wf.getnframes() / framerate) if framerate > 0 else -1

            rec = KaldiRecognizer(_model, wf.getframerate())
            rec.SetWords(True)

            results = []

            # Read the audio in chunks of 4000 frames (standard for Vosk)
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    # AcceptWaveform returns True when an utterance is complete (a pause)
                    part = json.loads(rec.Result())
                    results.append(part.get("text", ""))

            # Get the remaining audio after the last pause
            final = json.loads(rec.FinalResult())
            results.append(final.get("text", ""))

            # Stitch it all together, filtering out any empty strings
            full_text = " ".join(filter(None, results)).strip()

        t_end = timer()
        print(f"executed in: {(t_end - t_start):.6f}s, "
              f"audio duration: {duration:.6f}s, "
              f"ratio: {((t_end - t_start) / duration):.6f}s"")")

        return jsonify({"text": full_text})

    except wave.Error as e:
        return jsonify({"error": f"Invalid WAV file: {e}"}), 400


# Start "heating up" immediately
threading.Thread(target=load_model, daemon=True).start()


if __name__ == "__main__":
    # Host 0.0.0.0 is necessary for Docker communication
    app.run(host="0.0.0.0", port=args.port)
