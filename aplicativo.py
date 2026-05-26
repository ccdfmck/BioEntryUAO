from flask import Flask, render_template, Response, jsonify, request, redirect, url_for
import cv2
import os
import numpy as np
import faiss
from deepface import DeepFace
import sqlite3
from datetime import datetime
import shutil
import logging
import uuid
import imghdr
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ============================================
# OCULTAR SPAM DE REQUESTS FLASK
# ============================================

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ============================================
# SQLITE
# ============================================

conn = sqlite3.connect("usuarios.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS accesos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT,
    codigo    TEXT,
    resultado TEXT,
    confianza REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

# ============================================
# CONFIG
# ============================================

DB_PATH   = "database"
THRESHOLD = 0.6
OPERADORES_JSON = "operadores.json"

# ============================================
# FUNCIONES OPERADORES (JSON)
# ============================================

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
# CREAR OPERADOR ADMIN SI NO EXISTE
# ============================================

if not os.path.exists(OPERADORES_JSON):
    with open(OPERADORES_JSON, "w", encoding="utf-8") as f:
        json.dump([{
            "nombre":   "Administrador",
            "usuario":  "admin",
            "correo":   "admin@uao.edu.co",
            "rol":      "Administrador",
            "password": generate_password_hash("1234")
        }], f, indent=2)
    print("Operador creado: admin / 1234")

# ============================================
# ESTADO GLOBAL DE EMBEDDINGS
# ============================================

embeddings_store = {
    "embeddings": None,
    "labels":     [],
    "index":      None
}

def load_embeddings():

    embeddings = []
    labels     = []

    print("\nCargando base de rostros...\n")

    for file in os.listdir(DB_PATH):

        if not file.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        path = os.path.join(DB_PATH, file)

        try:

            objs = DeepFace.represent(
                img_path=path,
                model_name="ArcFace",
                detector_backend="retinaface",
                enforce_detection=False
            )

            if objs:

                embeddings.append(objs[0]["embedding"])

                labels.append(os.path.splitext(file)[0])

                print(f"✓ Cargado: {os.path.splitext(file)[0]}")

        except Exception as e:

            print("Error:", e)

    if not embeddings:

        print("⚠️ No se cargaron embeddings.")
        return

    emb_arr = np.array(embeddings).astype("float32")

    faiss.normalize_L2(emb_arr)

    idx = faiss.IndexFlatIP(emb_arr.shape[1])

    idx.add(emb_arr)

    embeddings_store["embeddings"] = emb_arr
    embeddings_store["labels"]     = labels
    embeddings_store["index"]      = idx

    print(f"\nFAISS listo — {len(labels)} persona(s)\n")

load_embeddings()

# ============================================
# MÉTRICAS
# ============================================

metrics = {
    "total_ok":   0,
    "total_deny": 0
}

# ============================================
# RECARGAR EMBEDDINGS
# ============================================

def recargar_embeddings():
    load_embeddings()


# ============================================
# WEBCAM
# ============================================

camera = cv2.VideoCapture(0)

camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

face_data = {
    "detected": False
}

# PERSONA ACTUAL FRENTE A CÁMARA
current_person = None

# ============================================
# VIDEO STREAM
# ============================================

def generate_frames():

    global face_data
    global current_person

    frame_count = 0

    while True:

        success, frame = camera.read()

        if not success:
            break

        frame_count += 1

        # espejo
        frame = cv2.flip(frame, 1)

        # ============================================
        # ANALIZAR CADA 15 FRAMES
        # ============================================

        if frame_count % 15 == 0:

            try:

                objs = DeepFace.represent(
                    img_path=frame,
                    model_name="ArcFace",
                    detector_backend="opencv",
                    enforce_detection=False
                )

                index  = embeddings_store["index"]
                labels = embeddings_store["labels"]

                # ============================================
                # NO HAY ROSTRO
                # ============================================

                if not objs or index is None:

                    face_data = {
                        "detected": False
                    }

                    current_person = None

                else:

                    obj = objs[0]

                    embedding   = obj["embedding"]
                    facial_area = obj["facial_area"]

                    x = facial_area["x"]
                    y = facial_area["y"]
                    w = facial_area["w"]
                    h = facial_area["h"]

                    vec = np.array([embedding]).astype("float32")

                    faiss.normalize_L2(vec)

                    # ============================================
                    # BUSCAR EN FAISS
                    # ============================================

                    D, I = index.search(vec, 1)

                    sim  = float(D[0][0])

                    conf = round(sim * 100, 2)

                    # ============================================
                    # RECONOCIDO
                    # ============================================

                    if sim > THRESHOLD:

                        name = labels[I[0][0]]

                        cursor.execute(
                            "SELECT nombre, codigo, rol, programa "
                            "FROM usuarios WHERE archivo LIKE ?",
                            (f"{name}%",)
                        )

                        user = cursor.fetchone()

                        if user:

                            nombre_real, codigo, rol, programa = user

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
                            "confidence": conf,
                            "x": int(x),
                            "y": int(y),
                            "w": int(w),
                            "h": int(h)
                        }

                        # ============================================
                        # SOLO REGISTRAR SI ES NUEVA PERSONA
                        # ============================================

                        if current_person != nombre_real:

                            print(f"\n✓ ACCESO APROBADO: {nombre_real} | {conf}%")

                            _log_access(
                                nombre_real,
                                codigo,
                                "aprobado",
                                conf
                            )

                            current_person = nombre_real

                    # ============================================
                    # DESCONOCIDO
                    # ============================================

                    else:

                        if sim > 0.15:

                            face_data = {
                                "detected": True,
                                "approved": False,
                                "name": "Desconocido",
                                "codigo": "N/A",
                                "rol": "No registrado",
                                "programa": "Acceso denegado",
                                "confidence": conf,
                                "x": int(x),
                                "y": int(y),
                                "w": int(w),
                                "h": int(h)
                            }

                            if current_person != "Desconocido":

                                print(f"\n✗ ACCESO DENEGADO")

                                _log_access(
                                    "Desconocido",
                                    "N/A",
                                    "denegado",
                                    conf
                                )

                                current_person = "Desconocido"

                        else:

                            face_data = {
                                "detected": False
                            }

                            current_person = None

            except Exception as e:

                print("Error:", e)

        # ============================================
        # DIBUJAR RESULTADO
        # ============================================

        if face_data.get("detected"):

            x = face_data["x"]
            y = face_data["y"]
            w = face_data["w"]
            h = face_data["h"]

            color = (
                (0, 255, 0)
                if face_data["approved"]
                else (0, 0, 255)
            )

            cv2.rectangle(
                frame,
                (x, y),
                (x + w, y + h),
                color,
                2
            )

            cv2.putText(
                frame,
                face_data["name"],
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

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )

# ============================================
# HELPER: LOG ACCESS
# ============================================

def _log_access(nombre, codigo, resultado, confianza):

    cursor.execute(
        "INSERT INTO accesos (nombre, codigo, resultado, confianza) VALUES (?, ?, ?, ?)",
        (nombre, codigo, resultado, confianza)
    )

    conn.commit()

    if resultado == "aprobado":

        metrics["total_ok"] += 1

    else:

        metrics["total_deny"] += 1

# ============================================
# ROUTES — VISTAS
# ============================================

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
def index_page():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            nombre   = request.form.get('nombre', '').strip()
            apellido = request.form.get('apellido', '').strip()
            codigo   = request.form.get('codigo', '').strip()
            programa = request.form.get('programa', '').strip()
            foto     = request.files.get('foto')

            # Validar campos obligatorios
            if not all([nombre, apellido, codigo, programa]):
                return jsonify({"ok": False, "error": "Todos los campos son obligatorios"}), 400

            if not foto:
                return jsonify({"ok": False, "error": "No se recibió la foto"}), 400

            # Validar que sea una imagen real (leer bytes para imghdr)
            foto_bytes = foto.read()
            tipo = imghdr.what(None, h=foto_bytes)
            if tipo not in ('jpeg', 'png', 'gif', 'webp'):
                return jsonify({"ok": False, "error": "El archivo no es una imagen válida"}), 400

            # Extensión normalizada
            ext = 'jpg' if tipo == 'jpeg' else tipo

            # Nombre seguro con UUID
            nombre_archivo = f"{uuid.uuid4().hex}.{ext}"
            ruta_foto      = os.path.join(DB_PATH, nombre_archivo)
            # Guardar desde bytes ya leídos
            with open(ruta_foto, 'wb') as f:
                f.write(foto_bytes)

            # Verificar duplicado por código
            cursor.execute("SELECT id FROM usuarios WHERE codigo = ?", (codigo,))
            if cursor.fetchone():
                return jsonify({"ok": False, "error": "El código ya está registrado"}), 409

            # Insertar solo las columnas que existen en la tabla
            cursor.execute("""
                INSERT INTO usuarios (nombre, codigo, rol, programa, archivo)
                VALUES (?, ?, ?, ?, ?)
            """, (f"{nombre} {apellido}", codigo, "Estudiante", programa, nombre_archivo))
            conn.commit()

            recargar_embeddings()

            return jsonify({"ok": True})

        except Exception as e:
            print("ERROR EN REGISTER:", e)
            return jsonify({"ok": False, "error": str(e)}), 500

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

@app.route("/video")
def video():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/face_data")
def get_face_data():

    return jsonify(face_data)

@app.route("/metrics")
def get_metrics():

    cursor.execute(
        "SELECT COUNT(*) FROM accesos WHERE resultado='aprobado'"
    )

    total_ok = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM accesos WHERE resultado='denegado'"
    )

    total_deny = cursor.fetchone()[0]

    cursor.execute(
        "SELECT nombre, codigo, resultado, confianza, timestamp "
        "FROM accesos "
        "ORDER BY id DESC LIMIT 6"
    )

    rows = cursor.fetchall()

    history = [
        {
            "nombre":    r[0],
            "codigo":    r[1],
            "resultado": r[2],
            "confianza": r[3],
            "timestamp": r[4]
        }
        for r in rows
    ]

    return jsonify({
        "registered": len(embeddings_store["labels"]),
        "total_ok":   total_ok,
        "total_deny": total_deny,
        "history":    history
    })

# ============================================
# ROUTES — ADMIN
# ============================================

ADMIN_PASSWORD = "uao2026"

@app.route("/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json()

    if data.get("password") == ADMIN_PASSWORD:

        return jsonify({"ok": True})

    return jsonify({
        "ok": False,
        "error": "Contraseña incorrecta"
    }), 401

@app.route("/admin/usuarios")
def admin_usuarios():

    cursor.execute(
        "SELECT id, nombre, codigo, rol, programa, archivo "
        "FROM usuarios ORDER BY id DESC"
    )

    rows = cursor.fetchall()

    return jsonify([
        {
            "id": r[0],
            "nombre": r[1],
            "codigo": r[2],
            "rol": r[3],
            "programa": r[4],
            "archivo": r[5]
        }
        for r in rows
    ])

@app.route("/admin/agregar", methods=["POST"])
def admin_agregar():

    nombre   = request.form.get("nombre", "").strip()
    codigo   = request.form.get("codigo", "").strip()
    rol      = request.form.get("rol", "").strip()
    programa = request.form.get("programa", "").strip()
    foto     = request.files.get("foto")

    if not all([nombre, codigo, rol, programa, foto]):

        return jsonify({
            "ok": False,
            "error": "Faltan campos"
        }), 400

    nombre_archivo = (
        nombre.replace(" ", "") +
        os.path.splitext(foto.filename)[1]
    )

    ruta_foto = os.path.join(DB_PATH, nombre_archivo)

    foto.save(ruta_foto)

    try:

        cursor.execute(
            "INSERT INTO usuarios "
            "(nombre, codigo, rol, programa, archivo) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                nombre,
                codigo,
                rol,
                programa,
                nombre_archivo
            )
        )

        conn.commit()

    except sqlite3.IntegrityError:

        os.remove(ruta_foto)

        return jsonify({
            "ok": False,
            "error": "El usuario ya existe"
        }), 409

    load_embeddings()

    return jsonify({
        "ok": True,
        "archivo": nombre_archivo
    })

@app.route("/admin/eliminar/<int:uid>", methods=["DELETE"])
def admin_eliminar(uid):

    cursor.execute(
        "SELECT archivo FROM usuarios WHERE id = ?",
        (uid,)
    )

    row = cursor.fetchone()

    if not row:

        return jsonify({
            "ok": False,
            "error": "Usuario no encontrado"
        }), 404

    archivo = row[0]

    ruta = os.path.join(DB_PATH, archivo)

    if os.path.exists(ruta):

        os.remove(ruta)

    cursor.execute(
        "DELETE FROM usuarios WHERE id = ?",
        (uid,)
    )

    conn.commit()

    load_embeddings()

    return jsonify({"ok": True})

# ============================================
# RUN
# ============================================

if __name__ == "__main__":

    print("\n=== BIOENTRY INICIADO ===\n")

    app.run(debug=True)