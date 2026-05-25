from flask import Flask, render_template, Response, jsonify
import cv2
import os
import numpy as np
import faiss
<<<<<<< HEAD
from deepface import DeepFace
=======
import json
from werkzeug.security import generate_password_hash, check_password_hash

OPERADORES_JSON = "operadores.json"

from deepface import DeepFace
# Cambia esto:
from flask import Flask, render_template, Response, jsonify, request

>>>>>>> origin/silva
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

<<<<<<< HEAD
@app.route("/")
def home():
    return render_template("index.html")

=======

from flask import Flask, render_template, Response, jsonify, request, redirect, url_for

def recargar_embeddings():
    global embeddings, labels, index
    nuevos_embeddings = []
    nuevos_labels = []

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
                nuevos_embeddings.append(objs[0]["embedding"])
                nuevos_labels.append(os.path.splitext(file)[0])
        except Exception as e:
            print("Error recargando:", e)

    nuevos_embeddings = np.array(nuevos_embeddings).astype("float32")
    nuevo_index = faiss.IndexFlatL2(nuevos_embeddings.shape[1])
    nuevo_index.add(nuevos_embeddings)

    embeddings = nuevos_embeddings
    labels     = nuevos_labels
    index      = nuevo_index
    print(f"Embeddings recargados. Total: {len(labels)}")

@app.route('/')
def root():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data     = request.get_json()
        usuario  = data.get('usuario')
        password = data.get('password')

        operador = buscar_operador(usuario, password)
        if operador:
            return jsonify({"ok": True, "rol": operador["rol"]})
        return jsonify({"ok": False, "error": "Credenciales incorrectas"}), 401

    return render_template('login.html')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])   # ← una sola ruta con ambos métodos
def register():
    if request.method == 'POST':
        nombre   = request.form.get('nombre')
        apellido = request.form.get('apellido')
        codigo   = request.form.get('codigo')
        programa = request.form.get('programa')
        correo   = request.form.get('correo')
        foto     = request.files.get('foto')
        foto.save(f"database/{nombre}{apellido}.jpg")
        return jsonify({"ok": True})
    return render_template('register.html')

@app.route('/register_operador', methods=['GET', 'POST'])
def register_operador():
    if request.method == 'POST':
        data     = request.get_json()
        nombre   = data.get('nombre')
        apellido = data.get('apellido')
        usuario  = data.get('usuario')
        correo   = data.get('correo')
        rol      = data.get('rol')
        password = data.get('password')

        if usuario_existe(usuario):
            return jsonify({"ok": False, "error": f"El usuario '{usuario}' ya existe"}), 409

        operadores = cargar_operadores()
        operadores.append({
            "nombre":   f"{nombre} {apellido}",
            "usuario":  usuario,
            "correo":   correo,
            "rol":      rol,
            "password": generate_password_hash(password)
        })
        guardar_operadores(operadores)
        return jsonify({"ok": True})

    return render_template('register_operador.html')

with open("operadores.json", "w") as f:
    json.dump([{
        "nombre": "Administrador",
        "usuario": "admin",
        "correo": "admin@uao.edu.co",
        "rol": "Administrador",
        "password": generate_password_hash("1234")
    }], f, indent=2)

print("Operador creado: admin / 1234")

>>>>>>> origin/silva
@app.route("/video")
def video():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/face_data")


def get_face_data():
    return jsonify(face_data)

# ← línea en blanco aquí, fuera de la función anterior

def cargar_operadores():
    if not os.path.exists(OPERADORES_JSON):
        return []
    with open(OPERADORES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_operadores(operadores):
    with open(OPERADORES_JSON, "w", encoding="utf-8") as f:
        json.dump(operadores, f, ensure_ascii=False, indent=2)

def buscar_operador(usuario, password):
    operadores = cargar_operadores()
    for op in operadores:
        if op["usuario"] == usuario and check_password_hash(op["password"], password):
            return op
    return None

def usuario_existe(usuario):
    operadores = cargar_operadores()
    return any(op["usuario"] == usuario for op in operadores)
# ============================================
# RUN
# ============================================

if __name__ == "__main__":
    app.run(debug=True)