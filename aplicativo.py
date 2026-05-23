from flask import Flask, render_template, Response, jsonify

import cv2
import faiss
import pickle
import sqlite3
import numpy as np

from deepface import DeepFace

# =========================
# APP
# =========================

app = Flask(__name__)

# =========================
# LOAD FAISS
# =========================

index = faiss.read_index("faiss_index.bin")

with open("embeddings.pkl", "rb") as f:
    names = pickle.load(f)

# =========================
# SQLITE
# =========================

conn = sqlite3.connect("faces.db", check_same_thread=False)

cursor = conn.cursor()

# =========================
# CAMERA
# =========================

camera = cv2.VideoCapture(0)

# =========================
# FACE DATA
# =========================

current_data = {
    "detected": False,
    "name": "",
    "confidence": 0
}

# =========================
# FRAMES
# =========================

def generate_frames():

    global current_data

    while True:

        success, frame = camera.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        try:

            embedding = DeepFace.represent(
                img_path=frame,
                model_name="ArcFace",
                detector_backend="retinaface",
                enforce_detection=False
            )

            if len(embedding) > 0:

                vector = np.array(
                    [embedding[0]["embedding"]],
                    dtype="float32"
                )

                distances, indices = index.search(vector, 1)

                best_match = indices[0][0]

                distance = distances[0][0]

                name = names[best_match]

                confidence = int(100 - distance)

                if confidence < 0:
                    confidence = 0

                if confidence > 100:
                    confidence = 100

                current_data["detected"] = True
                current_data["name"] = name
                current_data["confidence"] = confidence

                cv2.putText(
                    frame,
                    f"{name} ({confidence}%)",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2
                )

            else:

                current_data["detected"] = False

        except Exception as e:

            print(e)

            current_data["detected"] = False

        ret, buffer = cv2.imencode(".jpg", frame)

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )

# =========================
# ROUTES
# =========================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/face_data')
def face_data():
    return jsonify(current_data)

# =========================
# MAIN
# =========================

if __name__ == "__main__":

    app.run(debug=True)