from flask import Flask, request, send_from_directory, jsonify, render_template_string
import os
import sqlite3

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
DB_PATH = 'Documentos.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Inicializar base de datos
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS archivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL
            )
        ''')

init_db()

@app.route('/')
def index():
    return render_template_string(open('templates/index.html', encoding='utf-8').read())

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No se encontró el archivo.', 400
    file = request.files['file']
    if file.filename == '':
        return 'Nombre de archivo vacío.', 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)
    with sqlite3.connect(DB_PATH) as conn:
        try:
            conn.execute("INSERT INTO archivos (nombre) VALUES (?)", (file.filename,))
        except sqlite3.IntegrityError:
            pass
    return 'Archivo subido correctamente.'

@app.route('/files', methods=['GET'])
def list_files():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT nombre FROM archivos")
        archivos = [row[0] for row in cursor.fetchall()]
    return jsonify(archivos)

@app.route('/uploads/<filename>', methods=['GET'])
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM archivos WHERE nombre = ?", (filename,))
        return 'Archivo eliminado.'
    return 'Archivo no encontrado.', 404

@app.route('/rename', methods=['PUT'])
def rename_file():
    data = request.get_json(force=True)
    if not data:
        return "No se recibió información JSON.", 400

    old_name = data.get("old_name")
    new_name = data.get("new_name")

    if not old_name or not new_name:
        return "Se requiere el nombre antiguo y el nuevo nombre", 400

    old_path = os.path.join(UPLOAD_FOLDER, old_name)
    new_path = os.path.join(UPLOAD_FOLDER, new_name)

    if not os.path.exists(old_path):
        return "El archivo original no existe.", 404
    if os.path.exists(new_path):
        return "Ya existe un archivo con ese nombre.", 400

    os.rename(old_path, new_path)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE archivos SET nombre = ? WHERE nombre = ?", (new_name, old_name))

    return "Nombre actualizado correctamente."

if __name__ == '__main__':
    app.run(debug=True, port=8000)
