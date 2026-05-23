import os
import cv2
import faiss
import pickle
import sqlite3
import numpy as np

from deepface import DeepFace

# =========================
# CONFIG
# =========================

DATABASE_FOLDER = "database"

# =========================
# SQLITE
# =========================

conn = sqlite3.connect("faces.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    image_path TEXT
)
""")

conn.commit()

# =========================
# EMBEDDINGS
# =========================

embeddings = []
names = []

# =========================
# RECORRER IMÁGENES
# =========================

for file in os.listdir(DATABASE_FOLDER):

    if not file.lower().endswith((".jpg", ".jpeg", ".png")):
     continue

    path = os.path.join(DATABASE_FOLDER, file)

    print("Procesando:", path)

    try:

        embedding = DeepFace.represent(
            img_path=path,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=False
        )

        vector = embedding[0]["embedding"]

        embeddings.append(vector)

        # nombre limpio
        name = os.path.splitext(file)[0]

        names.append(name)

        # guardar sqlite
        cursor.execute(
            "INSERT INTO users (name, image_path) VALUES (?, ?)",
            (name, path)
        )

        conn.commit()

    except Exception as e:

        print("ERROR:", e)

# =========================
# FAISS
# =========================

embeddings = np.array(embeddings).astype("float32")

dimension = embeddings.shape[1]

index = faiss.IndexFlatL2(dimension)

index.add(embeddings)

# guardar índice
faiss.write_index(index, "faiss_index.bin")

# guardar nombres
with open("embeddings.pkl", "wb") as f:

    pickle.dump(names, f)

print("FAISS creado correctamente")