from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploaded'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/ecommerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Necesario para usar flash messages

db = SQLAlchemy(app)


# Definición de modelos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    correo = db.Column(db.String(100), unique=True)
    contraseña = db.Column(db.String(255))

    def set_password(self, password):
        self.contraseña = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contraseña, password)


class Producto(db.Model):
    __tablename__ = 'producto'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    precio = db.Column(db.Float)
    descripcion = db.Column(db.Text)
    imagen = db.Column(db.String(255))


class Carrito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    producto_id = db.Column(db.Integer, db.ForeignKey('producto.id'))
    cantidad = db.Column(db.Integer)


class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    fecha_pedido = db.Column(db.DateTime)
    total = db.Column(db.Float)
    estado = db.Column(db.String(20), default='pendiente')


# Rutas y vistas
@app.route('/')
def index():
    productos = Producto.query.all()  # Obtener todos los productos de la base de datos
    return render_template('index.html', productos=productos)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        contraseña = request.form['contraseña']

        usuario = Usuario(nombre=nombre, correo=correo)
        usuario.set_password(contraseña)

        db.session.add(usuario)
        db.session.commit()

        flash('Usuario registrado exitosamente', 'success')
        return redirect(url_for('login'))

    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and usuario.check_password(contraseña):
            session['usuario_id'] = usuario.id
            session['correo'] = usuario.correo
            flash('Login exitoso', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')

    return render_template('login.html')


@app.route('/panel_admin')
def panel_admin():
    if 'correo' not in session:
        return redirect(url_for('login'))

    productos = Producto.query.all()
    return render_template('panel_admin.html', productos=productos)


@app.route('/productos')
def mostrar_productos():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)


@app.route('/carrito')
def mostrar_carrito():
    productos_carrito = [
        {'nombre': 'Zapatos Nike', 'precio': 100, 'cantidad': 2},
        {'nombre': 'Camisa Adidas', 'precio': 50, 'cantidad': 1},
    ]
    total_carrito = sum(item['precio'] * item['cantidad'] for item in productos_carrito)
    return render_template('carrito.html', productos_carrito=productos_carrito, total_carrito=total_carrito)


@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        descripcion = request.form['descripcion']
        imagen = request.files.get('imagen')

        if imagen:
            upload_folder = os.path.join(app.root_path, 'uploaded')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            imagen_path = os.path.join(upload_folder, imagen.filename)
            imagen.save(imagen_path)
            imagen_relative_path = os.path.relpath(imagen_path, app.root_path)

        nuevo_producto = Producto(nombre=nombre, precio=precio, descripcion=descripcion, imagen=imagen_relative_path)
        db.session.add(nuevo_producto)
        db.session.commit()

        return redirect(url_for('mostrar_productos'))

    return render_template('agregar_producto.html')


@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.precio = request.form['precio']
        producto.descripcion = request.form['descripcion']

        nueva_imagen = request.files.get('imagen')
        if nueva_imagen:
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], nueva_imagen.filename)
            nueva_imagen.save(imagen_path)
            producto.imagen = imagen_path

        db.session.commit()
        return redirect(url_for('mostrar_productos'))

    return render_template('editar_producto.html', producto=producto)


@app.route('/uploaded/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/eliminar_producto/<int:producto_id>', methods=['POST'])
def eliminar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)
    db.session.delete(producto)
    db.session.commit()
    flash('Producto eliminado exitosamente', 'success')
    return redirect(url_for('mostrar_productos'))


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    session.pop('correo', None)
    flash('Has cerrado sesión exitosamente', 'success')
    return redirect(url_for('index'))


# Rutas de API
@app.route('/api/productos', methods=['GET'])
def api_productos():
    productos = Producto.query.all()
    productos_list = [
        {'id': producto.id, 'nombre': producto.nombre, 'precio': producto.precio, 'descripcion': producto.descripcion,
         'imagen': producto.imagen}
        for producto in productos
    ]
    return jsonify(productos_list)


@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    correo = data.get('correo')
    contraseña = data.get('contraseña')
    usuario = Usuario.query.filter_by(correo=correo).first()

    if usuario and usuario.check_password(contraseña):
        return jsonify({'mensaje': 'Login exitoso', 'usuario_id': usuario.id}), 200
    else:
        return jsonify({'mensaje': 'Correo o contraseña incorrectos'}), 401


@app.route('/api/usuarios', methods=['GET'])
def api_get_usuarios():
    usuarios = Usuario.query.all()
    usuarios_list = [
        {'id': usuario.id, 'nombre': usuario.nombre, 'correo': usuario.correo}
        for usuario in usuarios
    ]
    return jsonify(usuarios_list)


@app.route('/api/usuarios/<int:id>', methods=['GET'])
def api_get_usuario(id):
    usuario = Usuario.query.get(id)
    if usuario:
        return jsonify({'id': usuario.id, 'nombre': usuario.nombre, 'correo': usuario.correo})
    else:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404


@app.route('/api/usuarios', methods=['POST'])
def api_create_usuario():
    data = request.json
    nombre = data.get('nombre')
    correo = data.get('correo')
    contraseña = data.get('contraseña')

    if Usuario.query.filter_by(correo=correo).first():
        return jsonify({'mensaje': 'Correo ya registrado'}), 400

    usuario = Usuario(nombre=nombre, correo=correo)
    usuario.set_password(contraseña)
    db.session.add(usuario)
    db.session.commit()

    return jsonify({'mensaje': 'Usuario creado exitosamente', 'id': usuario.id}), 201


@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def api_update_usuario(id):
    data = request.json
    nombre = data.get('nombre')
    correo = data.get('correo')
    contraseña = data.get('contraseña')

    usuario = Usuario.query.get(id)
    if usuario:
        if nombre:
            usuario.nombre = nombre
        if correo:
            usuario.correo = correo
        if contraseña:
            usuario.set_password(contraseña)
        db.session.commit()
        return jsonify({'mensaje': 'Usuario actualizado exitosamente'})
    else:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404


@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def api_delete_usuario(id):
    usuario = Usuario.query.get(id)
    if usuario:
        db.session.delete(usuario)
        db.session.commit()
        return jsonify({'mensaje': 'Usuario eliminado exitosamente'})
    else:
        return jsonify({'mensaje': 'Usuario no encontrado'}), 404


if __name__ == '__main__':
    app.run(debug=True)
