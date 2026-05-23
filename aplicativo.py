from flask import Flask, render_template, Response, jsonify
import cv2
import os
import tempfile
import numpy as np
import faiss

from deepface import DeepFace

import sqlite3

app = Flask(__name__)

conn = sqlite3.connect("usuarios.db", check_same_thread=False)

cursor = conn.cursor()

# ============================================
# CONFIG
# ============================================

DB_PATH = "database"

THRESHOLD = 120

# ============================================
# FAISS
# ============================================

embeddings = []
labels = []

print("Cargando base de rostros...")

for file in os.listdir(DB_PATH):

    path = os.path.join(DB_PATH, file)

    try:

        objs = DeepFace.represent(
            img_path=path,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=False
        )

        if len(objs) > 0:

            embedding = objs[0]["embedding"]

            embeddings.append(embedding)

            name = os.path.splitext(file)[0]

            labels.append(name)

            print(f"Cargado: {name}")

    except Exception as e:
        print("Error:", e)

embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

print("FAISS listo")
print("Personas registradas:", len(labels))

# ============================================
# WEBCAM
# ============================================

camera = cv2.VideoCapture(0)

face_data = {
    "detected": False
}

# ============================================
# VIDEO STREAM
# ============================================


def generate_frames():

    global face_data

    while True:

        success, frame = camera.read()

        if not success:
            break

        # ============================================
        # GUARDAR FRAME TEMPORAL
        # ============================================

        temp_path = tempfile.mktemp(suffix=".jpg")

        cv2.imwrite(temp_path, frame)

        try:

            objs = DeepFace.represent(
                img_path=temp_path,
                model_name="ArcFace",
                detector_backend="retinaface",
                enforce_detection=False
            )

            # ============================================
            # SI NO DETECTA
            # ============================================

            if len(objs) == 0:

                face_data = {
                    "detected": False
                }

            else:

                obj = objs[0]

                embedding = obj["embedding"]

                facial_area = obj["facial_area"]

                x = facial_area["x"]
                y = facial_area["y"]
                w = facial_area["w"]
                h = facial_area["h"]

                embedding = np.array([embedding], dtype="float32")

                # ============================================
                # BUSCAR EN FAISS
                # ============================================

                D, I = index.search(embedding, 1)

                distance = float(D[0][0])

                print("DISTANCIA:", distance)
                print("PERSONA:", labels[I[0][0]])

                confidence = max(0, 100 - (distance * 10))
                confidence = round(confidence, 2)

                # ============================================
                # SI RECONOCE
                # ============================================

                if distance < THRESHOLD:

                    name = labels[I[0][0]]

                    # ============================================
                    # SQLITE
                    # ============================================
                    archivo = name + ".jpg"

                    cursor.execute(
                          "SELECT nombre, codigo, rol, programa FROM usuarios WHERE archivo LIKE ?",
                          (f"{name}%",)
                          )

                    user = cursor.fetchone()

                    if user:

                            nombre_real = user[0]
                            codigo = user[1]
                            rol = user[2]
                            programa = user[3]

                    else:

                            nombre_real = name
                            codigo = "N/A"
                            rol = "N/A"
                            programa = "N/A"

                    face_data = {
                            "detected": True,
                            "name": nombre_real,
                            "codigo": codigo,
                            "rol": rol,
                            "programa": programa,
                            "confidence": confidence,
                            "x": int(x),
                            "y": int(y),
                            "w": int(w),
                            "h": int(h)
                        }

                        # DIBUJAR EN FRAME

                    cv2.rectangle(
                            frame,
                            (x, y),
                            (x + w, y + h),
                            (0, 255, 0),
                            2
                        )

                    cv2.putText(
                            frame,
                            f"{nombre_real} {confidence:.1f}%",
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.7,
                            (0, 255, 0),
                            2
                        )

                # ============================================
                # DESCONOCIDO
                # ============================================

                else:

                    face_data = {
                        "detected": False
                    }

                    cv2.rectangle(
                        frame,
                        (x, y),
                        (x + w, y + h),
                        (0, 0, 255),
                        2
                    )

                    cv2.putText(
                        frame,
                        "DESCONOCIDO",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2
                    )

        except Exception as e:
            print("Error:", e)

        # ============================================
        # BORRAR TEMP
        # ============================================

        if os.path.exists(temp_path):
            os.remove(temp_path)

        # ============================================
        # ENVIAR FRAME
        # ============================================

        ret, buffer = cv2.imencode(".jpg", frame)

        frame = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            frame +
            b"\r\n"
        )

# ============================================
# ROUTES
# ============================================


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/face_data")
def get_face_data():
    return jsonify(face_data)

# ============================================
# RUN
# ============================================


if __name__ == "__main__":
    app.run(debug=True)
