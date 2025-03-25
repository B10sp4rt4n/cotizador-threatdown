# database.py
import sqlite3
import os

DB_PATH = "crm_cotizaciones.sqlite"

def conectar_db():
    return sqlite3.connect(DB_PATH)

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()

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
            condiciones_comerciales TEXT
        )
    """)

    # Asegurar que la columna usuario_id exista
    columnas = [col[1] for col in cursor.execute("PRAGMA table_info(cotizaciones)").fetchall()]
    if "usuario_id" not in columnas:
        cursor.execute("ALTER TABLE cotizaciones ADD COLUMN usuario_id INTEGER")

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
