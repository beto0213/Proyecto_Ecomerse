from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask import send_from_directory


import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploaded'  # Nombre de la carpeta de uploads
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:@localhost/ecommerce_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Definición de modelos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    correo = db.Column(db.String(100), unique=True)
    contraseña = db.Column(db.String(255))

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
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/panel_admin')
def panel_admin():
    productos = Producto.query.all()
    return render_template('panel_admin.html', productos=productos)


@app.route('/productos')
def mostrar_productos():
    productos = Producto.query.all()
    return render_template('productos.html', productos=productos)

# Ruta para la página del carrito de compras
@app.route('/carrito')
def mostrar_carrito():
    productos_carrito = [
        {'nombre': 'Zapatos Nike', 'precio': 100, 'cantidad': 2},
        {'nombre': 'Camisa Adidas', 'precio': 50, 'cantidad': 1},
    ]
    total_carrito = sum(item['precio'] * item['cantidad'] for item in productos_carrito)
    return render_template('carrito.html', productos_carrito=productos_carrito, total_carrito=total_carrito)

# Ruta para el formulario de agregar productos


@app.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    if request.method == 'POST':
        nombre = request.form['nombre']
        precio = request.form['precio']
        descripcion = request.form['descripcion']

        # Obtener el archivo adjunto
        imagen = request.files.get('imagen')

        # Guardar la imagen en algún lugar
        if imagen:
            # Directorio donde se guardarán las imágenes
            upload_folder = os.path.join(app.root_path, 'uploaded')

            # Verificar si el directorio de uploaded existe, si no, crearlo
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            # Guardar la imagen en el directorio de uploaded
            imagen_path = os.path.join(upload_folder, imagen.filename)
            imagen.save(imagen_path)

            # Cambiar la ruta a relativa antes de almacenarla en la base de datos
            imagen_relative_path = os.path.relpath(imagen_path, app.root_path)

        # Crear el nuevo producto y guardarlo en la base de datos
        nuevo_producto = Producto(nombre=nombre, precio=precio, descripcion=descripcion, imagen=imagen_relative_path)
        db.session.add(nuevo_producto)
        db.session.commit()

        return redirect(url_for('mostrar_productos'))

    return render_template('agregar_producto.html')


@app.route('/editar_producto/<int:producto_id>', methods=['GET', 'POST'])
def editar_producto(producto_id):
    producto = Producto.query.get_or_404(producto_id)

    if request.method == 'POST':
        # Actualizar los campos del producto con los datos del formulario
        producto.nombre = request.form['nombre']
        producto.precio = request.form['precio']
        producto.descripcion = request.form['descripcion']

        # Guardar la imagen si se adjunta una nueva
        nueva_imagen = request.files.get('imagen')
        if nueva_imagen:
            # Guardar la imagen en el directorio de uploaded
            imagen_path = os.path.join(app.config['UPLOAD_FOLDER'], nueva_imagen.filename)
            nueva_imagen.save(imagen_path)

            # Actualizar la ruta de la imagen en el producto
            producto.imagen = imagen_path

        # Guardar los cambios en la base de datos
        db.session.commit()

        return redirect(url_for('mostrar_productos'))

    return render_template('editar_producto.html', producto=producto)


@app.route('/uploaded/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    app.run(debug=True)