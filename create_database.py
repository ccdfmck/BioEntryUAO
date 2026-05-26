import sqlite3
import os

#connectar
conn = sqlite3.connect("usuarios.db")
cursor = conn.cursor()

#crear la tabla
cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    codigo TEXT,
    rol TEXT,
    programa TEXT,
    archivo TEXT UNIQUE
)
""")

#nuevos usuarios
usuarios = [

    ("Lulu 99", "223001", "Estudiante", "Ingeniería Sistemas", "Lulu99.jpg"),

    ("Daniela Valverde Moreno", "223002", "Estudiante", "Ingeniería Mecatrónica", "DanielaValverdeMoreno.jpeg"),

    ("Juan David Silva Colorado", "2233003", "Estudiante", "Ingenieria Multimedia", "JuanDavidSilvaColorado.jpeg"),

    ("Migueol Angel Vanegas Daza", "2233004", "Estudiante", "Comunicación", "MiguelAngelVanegasDaza.jpeg")
]

#para insertar sin que se dupliquen 
for usuario in usuarios:

    nombre, codigo, rol, programa, archivo = usuario

    cursor.execute(
        "SELECT * FROM usuarios WHERE archivo=?",
        (archivo,)
    )

    existe = cursor.fetchone()

    if existe:
        print(f"⚠️ Ya existe: {archivo}")

    else:

        cursor.execute("""
        INSERT INTO usuarios
        (nombre, codigo, rol, programa, archivo)
        VALUES (?, ?, ?, ?, ?)
        """, usuario)

        print(f"Agregado: {nombre}")

#save
conn.commit()
conn.close()

print("\n Base de datos actualizada")