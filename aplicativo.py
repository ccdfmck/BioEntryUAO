from flask import Flask, render_template, Response, jsonify
import cv2
import os
import numpy as np
import faiss
from deepface import DeepFace
import sqlite3

app = Flask(__name__)

# ============================================
# SQLITE
# ============================================

conn = sqlite3.connect("usuarios.db", check_same_thread=False)
cursor = conn.cursor()

# ============================================
# CONFIG
# ============================================

DB_PATH = "database"

# menor = más estricto
THRESHOLD = 0.6

# ============================================
# CARGAR EMBEDDINGS
# ============================================

embeddings = []
labels = []

print("Cargando base de rostros...")

for file in os.listdir(DB_PATH):

    if not file.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    path = os.path.join(DB_PATH, file)

    try:

        objs = DeepFace.represent(
            img_path=path,
            model_name="ArcFace",
            detector_backend="opencv",
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

# NORMALIZAR
faiss.normalize_L2(embeddings)

dimension = embeddings.shape[1]

# ============================================
# FAISS
# ============================================

index = faiss.IndexFlatIP(dimension)

index.add(embeddings)

print("FAISS listo")
print("Personas registradas:", len(labels))

# ============================================
# WEBCAM
# ============================================

camera = cv2.VideoCapture(0)

# BAJAR RESOLUCIÓN PARA MENOS LAG
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

face_data = {
    "detected": False
}

# ============================================
# VIDEO STREAM
# ============================================

def generate_frames():

    global face_data

    frame_count = 0

    while True:

        success, frame = camera.read()

        if not success:
            break

        frame_count += 1

        # espejo
        frame = cv2.flip(frame, 1)

        # ============================================
        # SOLO ANALIZAR CADA 15 FRAMES
        # ============================================

        if frame_count % 15 == 0:

            try:

                objs = DeepFace.represent(
                    img_path=frame,
                    model_name="ArcFace",
                    detector_backend="opencv",
                    enforce_detection=False
                )

                # ============================================
                # NO HAY ROSTRO
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

                    embedding = np.array([embedding]).astype("float32")

                    # NORMALIZAR
                    faiss.normalize_L2(embedding)

                    # ============================================
                    # BUSCAR EN FAISS
                    # ============================================

                    D, I = index.search(embedding, 1)

                    similarity = float(D[0][0])

                    print("SIMILITUD:", similarity)
                    print("PERSONA:", labels[I[0][0]])

                    confidence = round(similarity * 100, 2)

                    # ============================================
                    # RECONOCIDO
                    # ============================================

                    if similarity > THRESHOLD:

                        name = labels[I[0][0]]

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
                            "approved": True,
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

                    # ============================================
                    # DESCONOCIDO
                    # ============================================

                    else:

                        # SOLO DENEGAR SI REALMENTE HAY UNA CARA

                        if similarity > 0.15:

                            face_data = {
                                "detected": True,
                                "approved": False,
                                "name": "Desconocido",
                                "codigo": "N/A",
                                "rol": "No registrado",
                                "programa": "Acceso denegado",
                                "confidence": confidence,
                                "x": int(x),
                                "y": int(y),
                                "w": int(w),
                                "h": int(h)
                            }

                        else:

                            # probablemente no hay rostro
                            face_data = {
                                "detected": False
                            }

            except Exception as e:
                print("Error:", e)

        # ============================================
        # DIBUJAR RESULTADO
        # ============================================

        if face_data["detected"]:

            x = face_data["x"]
            y = face_data["y"]
            w = face_data["w"]
            h = face_data["h"]

            # ============================================
            # COLOR
            # ============================================

            if face_data["approved"]:

                color = (0, 255, 0)

            else:

                color = (0, 0, 255)

            # ============================================
            # RECTÁNGULO
            # ============================================

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                color,
                2
            )

            # ============================================
            # TEXTO
            # ============================================

            cv2.putText(
                frame,
                f'{face_data["name"]}',
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                color,
                2
            )

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