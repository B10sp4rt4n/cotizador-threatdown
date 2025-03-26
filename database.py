import sqlite3
import os

# Definición global de la base de datos
DB_PATH = "crm_cotizaciones.sqlite"

def conectar_db():
    return sqlite3.connect(DB_PATH)

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()

    # Tabla de empresas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            razon_social TEXT,
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

    # Tabla de contactos (clientes)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contactos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido_paterno TEXT,
            apellido_materno TEXT,
            correo TEXT,
            telefono TEXT,
            empresa_id INTEGER,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        )
    """)

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

    # Tabla de cotizaciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            contacto_id INTEGER,
            propuesta TEXT,
            fecha TEXT,
            responsable TEXT,
            total_venta REAL,
            total_costo REAL,
            utilidad REAL,
            margen REAL,
            vigencia TEXT,
            condiciones_comerciales TEXT,
            usuario_id INTEGER,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            FOREIGN KEY (contacto_id) REFERENCES contactos(id),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
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
