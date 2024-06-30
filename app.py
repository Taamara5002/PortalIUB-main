from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
import mysql.connector as sql
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Función para cargar la ruta del archivo de credenciales
def get_service_account_file_path(file_name):
    try:
        json_file_path = os.path.abspath(file_name)
        print(f"Ruta absoluta del archivo JSON: {json_file_path}")  # Imprimir la ruta absoluta
        
        # Comprobar si el archivo existe y es accesible
        if os.path.isfile(json_file_path):
            print("El archivo JSON existe y es accesible.")
            return json_file_path
        else:
            raise FileNotFoundError(f"Error: No se encontró el archivo JSON en {json_file_path}")
    except Exception as e:
        print(f"Error al obtener la ruta del archivo JSON: {str(e)}")
        return None

# Ruta al archivo de credenciales de la cuenta de servicio
SERVICE_ACCOUNT_FILE = get_service_account_file_path(r"C:\Users\Jei\Documents\GitHub\PortalIUB-main\credentials.json")

if SERVICE_ACCOUNT_FILE:
    # Identificador del proyecto de Dialogflow
    PROJECT_ID = 'mani-avls'

    # Configuración de las credenciales de la cuenta de servicio
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    # Función para interactuar con Dialogflow
    def detect_intent_texts(project_id, session_id, texts, language_code):
        session = requests.Session()

        # URL de la API de Dialogflow
        url = f'https://dialogflow.googleapis.com/v2/projects/{project_id}/agent/sessions/{session_id}:detectIntent'

        # Asegúrate de que las credenciales están actualizadas
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)

        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }

        responses = []
        for text in texts:
            body = {
                "query_input": {
                    "text": {
                        "text": text,
                        "language_code": language_code
                    }
                }
            }

            response = session.post(url, headers=headers, json=body, verify=False)
            response.raise_for_status()
            responses.append(response.json())

        return responses

# Configuración de la base de datos MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_DATABASE'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'port': int(os.getenv('DB_PORT'))
}

try:
    conn = sql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT DATABASE()")
    row = cursor.fetchone()
    print("Conexión exitosa a la base de datos:", row)
    conn.close()
except Exception as e:
    print("Error al conectar a la base de datos:", e)

# Función para establecer la conexión con la base de datos MySQL
def get_database_connection():
    try:
        conn = sql.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None

# Función para validar las credenciales de inicio de sesión
def validate_login(correo, password):
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, password FROM users WHERE correo = %s", (correo,))
        user = cursor.fetchone()
        conn.close()
        if user and user[1] == password:
            return {'id': user[0]}
    return None

# Función para verificar si el correo ya está registrado
def email_exists(correo):
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE correo = %s", (correo,))
        user = cursor.fetchone()
        conn.close()
        return user is not None
    return False

# Función para modificar la longitud de la columna 'password'
def modify_password_column():
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("ALTER TABLE users MODIFY COLUMN password VARCHAR(255)")
            conn.commit()
            conn.close()
            print("La columna 'password' ha sido modificada correctamente.")
            return True
        else:
            print("Error: No se pudo conectar a la base de datos.")
            return False
    except Exception as e:
        print("Error al modificar la columna 'password':", e)
        return False

# Ruta para modificar la columna 'password'
@app.route('/modify_password_column')
def modify_column_route():
    if modify_password_column():
        return "Modificación de la columna 'password' realizada con éxito."
    else:
        return "Error al modificar la columna 'password'."

# Ruta principal del chat
@app.route('/')
def index():
    return render_template('index.html')

# Ruta para manejar las solicitudes del chat
@app.route('/send_message', methods=['POST'])
def send_message():
    if SERVICE_ACCOUNT_FILE:
        message = request.form['messageInput']
        session_id = 'unique_session_id'  # Puedes generar un ID de sesión único aquí

        texts = [message]
        language_code = 'es'

        # Obtener la respuesta de Dialogflow
        responses = detect_intent_texts(PROJECT_ID, session_id, texts, language_code)

        # Obtener todos los textos de cumplimiento de cada respuesta
        fulfillment_texts = []
        for response in responses:
            fulfillment_text = response.get('queryResult', {}).get('fulfillmentText', '')
            fulfillment_texts.append(fulfillment_text)

        return jsonify({'response': fulfillment_texts})
    else:
        message = request.form['messageInput']
        return jsonify({'response': f'Mensaje recibido: {message}'})

# Ruta para el formulario de inicio de sesión
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']

        # Validar las credenciales de inicio de sesión
        user = validate_login(correo, password)

        if user:
            session['user_id'] = user['id']  # Almacena el ID del usuario en la sesión
            return redirect(url_for('post_login'))
        else:
            flash('Credenciales incorrectas', 'error')

    return render_template('index.html')

# Ruta para la página post-login
@app.route('/post-login')
def post_login():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('post-login.html')

# Ruta para el formulario de registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        first_name = request.form['first_name']
        program = request.form['program']

        # Verificar si el correo ya está registrado
        if email_exists(correo):
            flash('El correo ya está registrado', 'error')
            return redirect(url_for('register'))
        
        # Validar el correo
        if not correo.endswith('@unibarranquilla.edu.co'):
            flash('El correo debe ser el correo institucional de la IUB', 'error')
            return redirect(url_for('register'))

        # Validar la contraseña
        if len(password) < 8 or not any(char.isupper() for char in password) or \
                not any(char.islower() for char in password) or not any(char.isdigit() for char in password) or \
                not any(char in '@$!%*?&' for char in password):
            flash('La contraseña debe tener al menos 8 caracteres, incluyendo una letra mayúscula, una letra minúscula, un número y un carácter especial.', 'error')
            return redirect(url_for('register'))

        # Llamar a la función para insertar usuario en la base de datos
        if InsertInTable_U((correo, password, first_name, program)):
            flash('Usuario registrado exitosamente', 'success')
            return redirect(url_for('index'))
        else:
            flash('Error al registrar usuario', 'error')

    return render_template('register.html')

# Función para insertar datos en la tabla 'users'
def InsertInTable_U(datos):
    try:
        conn = get_database_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (correo, password, first_name, program) 
                VALUES (%s, %s, %s, %s)
            """, datos)
            conn.commit()
            conn.close()
            print("Datos insertados correctamente.")
            return True
        else:
            print("Error: No se pudo conectar a la base de datos.")
            return False
    except Exception as e:
        print("Error al insertar datos:", e)
        return False

# Ruta para verificar si el correo ya está registrado
@app.route('/check_email', methods=['POST'])
def check_email():
    data = request.get_json()
    correo = data['correo']
    exists = email_exists(correo)
    return jsonify({'exists': exists})

# Ejecutar la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
