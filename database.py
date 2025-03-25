import sqlite3
import os

DB_PATH = "crm_cotizaciones.sqlite"

def conectar_db():
    return sqlite3.connect(DB_PATH)

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()

    # Tabla de usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            correo TEXT UNIQUE,
            contraseña TEXT,
            tipo_usuario TEXT,
            admin_id INTEGER,
            FOREIGN KEY (admin_id) REFERENCES usuarios(id)
        )
    """)

    # Tabla de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido_paterno TEXT,
            apellido_materno TEXT,
            empresa TEXT,
            correo TEXT,
            telefono TEXT,
            rfc TEXT,
            calle TEXT,
            numero_exterior TEXT,
            numero_interior TEXT,
            codigo_postal TEXT,
            municipio TEXT,
            ciudad TEXT,
            estado TEXT,
            notas TEXT
        )
    """)

    # Tabla de cotizaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            contacto TEXT,
            propuesta TEXT,
            fecha TEXT,
            responsable TEXT,
            total_venta REAL,
            total_costo REAL,
            utilidad REAL,
            margen REAL,
            vigencia TEXT,
            condiciones_comerciales TEXT,
            usuario_id INTEGER
        )
    """)

    # Tabla de productos relacionados a cotización
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotizacion_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            precio_total REAL,
            descuento_aplicado REAL,
            tipo_origen TEXT,
            FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
        )
    """)

    conn.commit()
    conn.close()

