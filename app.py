from flask import Flask, request, render_template, redirect, url_for, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurar base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)  # Nuevo campo
    password = db.Column(db.String(120), nullable=False)

# Crear la base de datos con datos iniciales
def init_db():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", email="admin@example.com", password="admin123")  # Incluir email
        db.session.add(admin)
        db.session.commit()

# Página introductoria
@app.route('/')
def home():
    return render_template('index.html')  # Página introductoria



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Buscar al usuario por nombre de usuario y contraseña
        user = User.query.filter_by(username=username, password=password).first()
        
        # Si el usuario existe, redirigir a la página protegida
        if user:
            resp = make_response(redirect(url_for('protected')))
            resp.set_cookie('username', username)
            return resp
        
        return "<h1>Credenciales inválidas</h1><a href='/login'>Intentar de nuevo</a>"

    # Si la solicitud es GET, mostramos el formulario de login con el archivo HTML
    return render_template('login.html')


# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return "<h1>El usuario o email ya existe</h1><a href='/register'>Intentar de nuevo</a>"
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# Contenido protegido
@app.route('/protected')
def protected():
    # Obtener el nombre de usuario desde la cookie
    user = request.cookies.get('username')
    
    # Si no hay usuario (es decir, no está logueado), redirigir a login
    if not user:
        return redirect(url_for('login'))
    
    # Si el usuario está logueado, mostrar la página empezar.html
    return render_template('empezar.html', username=user)

# Cerrar sesión
@app.route('/logout')
def logout():
    resp = make_response(redirect(url_for('home')))
    resp.set_cookie('username', '', expires=0)  # Eliminar cookies
    return resp
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nosotros')
def nosotros():
    return render_template('nosotros.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route('/carrito')
def carrito():
    return render_template('carrito.html')


@app.route('/empezar')
def empezar():
    return render_template('empezar.html')

@app.route('/reserva1')
def reserva1():
    return render_template('reserva1.html')

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



if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)