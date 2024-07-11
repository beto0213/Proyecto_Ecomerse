from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

@app.route('/')
def ver_productos():
    # Lógica para obtener todos los productos de tu base de datos
    productos = obtener_productos_desde_bd()
    return render_template('ver_productos.html', productos=productos)
