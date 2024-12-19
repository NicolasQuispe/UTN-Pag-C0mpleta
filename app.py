from flask import Flask, request, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Configurar base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

# Crear la base de datos con datos iniciales
def init_db():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash("admin123")
        admin = User(username="admin", email="admin@example.com", password=hashed_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()


def load_config():
    with open("config.json", "r", encoding="utf-8") as file:
        return json.load(file)
    
# Página introductoria
@app.route('/')
def index():
    data = load_config()  # Cargar los datos desde config.json
    return render_template('index.html', **data)




# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Buscar al usuario por nombre de usuario
        user = User.query.filter_by(username=username).first()
        
        if user:
            print(f"Usuario encontrado: {user.username}, Is Admin: {user.is_admin}")
            
            # Verificar contraseña cifrada
            if check_password_hash(user.password, password):
                if user.is_admin:
                    print("Usuario admin, redirigiendo a /admin")
                    resp = make_response(redirect(url_for('admin')))
                else:
                    print("Usuario normal, redirigiendo a /empezar")
                    resp = make_response(redirect(url_for('empezar')))
                
                # Configurar cookie
                resp.set_cookie('username', username)
                return resp
            else:
                print("Contraseña incorrecta")  # Depuración
        else:
            print("Usuario no encontrado")  # Depuración
        
        return "<h1>Credenciales inválidas</h1><a href='/login'>Intentar de nuevo</a>"

    return render_template('login.html')


# Página de administración
@app.route('/admin')
def admin():
    username = request.cookies.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and user.is_admin:
            return render_template('admin.html')
    return redirect(url_for('login'))

# Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Verificar si el usuario o correo ya existen
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return "<h1>El usuario o email ya existe</h1><a href='/register'>Intentar de nuevo</a>"
        
        # Cifrar la contraseña
        hashed_password = generate_password_hash(password)
        
        # Crear el nuevo usuario
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Contenido protegido (ahora redirige a 'empezar.html' en vez de 'protected.html')
@app.route('/protected')
def protected():
    username = request.cookies.get('username')
    if username:
        user = User.query.filter_by(username=username).first()
        if user and not user.is_admin:
            return render_template('protected.html')
    return redirect(url_for('login'))

# Página para usuarios normales
@app.route('/empezar')
def empezar():
    try:
        data = load_config()  # Cargar los datos desde config.json
        print("Datos cargados:", data)  # Imprime los datos en la consola
        return render_template('empezar.html', **data)  # Cargar empezar.html con los datos
    except Exception as e:
        print(f"Error cargando config.json: {e}")
        return "Error al cargar la configuración", 500
    

# Cerrar sesión
@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('index')))
    resp.set_cookie('username', '', expires=0)
    return resp

# Otras páginas
@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

#@app.route('/contacto')
#def contacto():
 #   return render_template('contacto.html')

@app.route('/carrito')
def carrito():
    return render_template('carrito.html')

#@app.route('/reserva1')


@app.route('/reserva2')
def reserva2():
    return render_template('reserva2.html')

@app.route('/confirmacion')
def confirmacion():
    fname = request.args.get('fname')
    lname = request.args.get('lname')
    email = request.args.get('email')
    message = request.args.get('message')
    return render_template('confirmacion.html', fname=fname, lname=lname, email=email, message=message)

@app.route('/debug')
def debug():
    users = User.query.all()
    result = []
    for user in users:
        result.append(f"Username: {user.username}, Email: {user.email}, Is Admin: {user.is_admin}, Password: {user.password}")
    return "<br>".join(result)

# Función para cargar el archivo config.json
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)

# Función para guardar el archivo config.json
def save_config(data):
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Ruta para mostrar el formulario
@app.route('/editar')
def editar():
    data = load_config()
    return render_template('admin.html', **data)

# Ruta para guardar los cambios
@app.route('/guardar', methods=["POST"])
def guardar():
    # Captura los datos del formulario
    data = {
        "banner_title": request.form['banner_title'],
        "package1_title": request.form['package1_title'],
       
        "package1_link": request.form['package1_link'],
        "package2_title": request.form['package2_title'],
        
        "package2_link": request.form['package2_link'],
        "facebook_link": request.form['facebook_link'],
        "twitter_link": request.form['twitter_link'],
        "instagram_link": request.form['instagram_link'],
        "footer_text": request.form['footer_text']
    }
    save_config(data)  # Guarda los datos en config.json
    return redirect(url_for('admin'))  # Redirige al formulario de edición

#................................................................
# Configuración del servidor SMTP
SMTP_SERVER = "smtp.gmail.com"  # Cambia esto si usas otro proveedor
SMTP_PORT = 587
SMTP_EMAIL = "reservapruebadisney@gmail.com"  # Cambia a tu correo
SMTP_PASSWORD = "habq fbut njof dilk"     # Cambia a tu contraseña

@app.route("/contacto")
def contacto():
    return render_template("contacto.html")  # Tu página principal

@app.route("/submit-contacto", methods=["POST"])
def submit_contacto():
    # Obtener los datos del formulario
    name = request.form["name"]
    email = request.form["email"]
    phone = request.form["phone"]
    date = request.form["date"]
    time = request.form["time"]
    message = request.form["message"]

    # Crear el mensaje para ti (administrador)
    admin_message = f"""
    Nueva Reserva Recibida:
    Nombre: {name}
    Correo Electrónico: {email}
    Teléfono: {phone}
    Fecha: {date}
    Hora: {time}
    Mensaje/Detalles: {message}
    """

    # Crear el mensaje para el cliente
    client_message = f"""
    Hola {name},
    
    Gracias por realizar tu reserva. Aquí tienes los detalles:
    Fecha: {date}
    Hora: {time}
    Mensaje/Detalles: {message}
    
    Nos pondremos en contacto contigo si necesitamos más información.
    """

    # Enviar los correos
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)

            # Enviar correo al administrador
            admin_email = MIMEMultipart()
            admin_email["From"] = SMTP_EMAIL
            admin_email["To"] = SMTP_EMAIL
            admin_email["Subject"] = "Nueva Reserva Recibida"
            admin_email.attach(MIMEText(admin_message, "plain"))
            server.sendmail(SMTP_EMAIL, SMTP_EMAIL, admin_email.as_string())

            # Enviar correo al cliente
            client_email = MIMEMultipart()
            client_email["From"] = SMTP_EMAIL
            client_email["To"] = email
            client_email["Subject"] = "Confirmación de Reserva"
            client_email.attach(MIMEText(client_message, "plain"))
            server.sendmail(SMTP_EMAIL, email, client_email.as_string())

        return "Reserva enviada correctamente. Revisa tu correo."
    except Exception as e:
        print("Error al enviar el correo:", e)
        return "Hubo un error al enviar la reserva. Por favor, intenta de nuevo."
    
    ################################################################

@app.route('/reserva1')
def reserva1():
    return render_template('reserva1.html')  # Asegúrate de que este archivo existe

from flask import render_template

@app.route('/submit-reservation1', methods=['POST'])
def submit_reservation1():
    # Obtener los datos del formulario
    travel_date = request.form.get('travel_date')
    return_date = request.form.get('return_date')
    name = request.form.get('name')
    surname = request.form.get('surname')
    birth_date = request.form.get('birth_date')
    phone = request.form.get('phone')
    email = request.form.get('email')

    # Crear el mensaje para la agencia
    agency_message = f"""
    Nueva Reserva Recibida:
    Fecha de Salida: {travel_date}
    Fecha de Regreso: {return_date}
    Pasajero: {name} {surname}
    Fecha de Nacimiento: {birth_date}
    Teléfono: {phone}
    Correo Electrónico: {email}
    """

    # Crear el mensaje para el cliente
    client_message = f"""
    Hola {name},

    Gracias por realizar tu reserva. Aquí tienes los detalles:
    Fecha de Salida: {travel_date}
    Fecha de Regreso: {return_date}
    Pasajero: {name} {surname}
    Fecha de Nacimiento: {birth_date}

    Por favor, acércate a nuestra sucursal para confirmar la reserva con esta información.

    Saludos,
    Tu Agencia de Viajes.
    """

    try:
        # Configurar el servidor SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)

        # Enviar correo a la agencia
        agency_email = "reservapruebadisney@gmail.com"  # Cambia por el correo de la agencia
        msg_to_agency = MIMEMultipart()
        msg_to_agency['From'] = SMTP_EMAIL
        msg_to_agency['To'] = agency_email
        msg_to_agency['Subject'] = "Nueva Reserva Recibida"
        msg_to_agency.attach(MIMEText(agency_message, 'plain'))
        server.sendmail(SMTP_EMAIL, agency_email, msg_to_agency.as_string())

        # Enviar correo al cliente
        msg_to_client = MIMEMultipart()
        msg_to_client['From'] = SMTP_EMAIL
        msg_to_client['To'] = email
        msg_to_client['Subject'] = "Confirmación de Reserva"
        msg_to_client.attach(MIMEText(client_message, 'plain'))
        server.sendmail(SMTP_EMAIL, email, msg_to_client.as_string())

        server.quit()

        # Pasar los detalles de la reserva al cliente para mostrar la página de confirmación
        return render_template('reserva1.html', travel_date=travel_date, return_date=return_date, 
                               name=name, surname=surname, birth_date=birth_date)

    except Exception as e:
        return f"Error al enviar el correo: {e}"

    
    

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
