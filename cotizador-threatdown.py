import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
from fpdf import FPDF

# Configuración de la base de datos
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")

# ========================
# Funciones de base de datos
# ========================
def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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

def conectar_db():
    return sqlite3.connect(DB_PATH)

def guardar_cotizacion(datos, productos_venta, productos_costo):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cotizaciones (
            cliente, contacto, propuesta, fecha, responsable,
            total_venta, total_costo, utilidad, margen, vigencia, condiciones_comerciales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["total_venta"], datos["total_costo"],
        datos["utilidad"], datos["margen"], datos["vigencia"], datos["condiciones_comerciales"]
    ))
    cotizacion_id = cursor.lastrowid

    for p in productos_venta:
        cursor.execute("""
            INSERT INTO detalle_productos (
                cotizacion_id, producto, cantidad, precio_unitario,
                precio_total, descuento_aplicado, tipo_origen
            ) VALUES (?, ?, ?, ?, ?, ?, 'venta')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Unitario Lista"],
            p["Subtotal"], p["Descuento %"]
        ))

    for p in productos_costo:
        cursor.execute("""
            INSERT INTO detalle_productos (
                cotizacion_id, producto, cantidad, precio_unitario,
                precio_total, descuento_aplicado, tipo_origen
            ) VALUES (?, ?, ?, ?, ?, ?, 'costo')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Base"],
            p["Subtotal"], p["Item Disc. %"] + p["Channel + Deal Disc. %"]
        ))

    conn.commit()
    conn.close()
    return cotizacion_id

def ver_historial():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM cotizaciones ORDER BY fecha DESC", conn)
    conn.close()
    return df

# Inicializar base de datos
inicializar_db()
