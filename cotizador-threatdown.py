import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
from fpdf import FPDF

DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")

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
            cargo TEXT,
            total_venta REAL,
            total_costo REAL,
            utilidad REAL,
            margen REAL
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
        INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable, cargo, total_venta, total_costo, utilidad, margen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["cargo"], datos["total_venta"], datos["total_costo"],
        datos["utilidad"], datos["margen"]
    ))
    cotizacion_id = cursor.lastrowid

    for p in productos_venta:
        cursor.execute("""
            INSERT INTO detalle_productos (cotizacion_id, producto, cantidad, precio_unitario, precio_total, descuento_aplicado, tipo_origen)
            VALUES (?, ?, ?, ?, ?, ?, 'venta')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Unitario de Lista"],
            p["Precio Total con Descuento"], p["Descuento %"]
        ))

    for p in productos_costo:
        cursor.execute("""
            INSERT INTO detalle_productos (cotizacion_id, producto, cantidad, precio_unitario, precio_total, descuento_aplicado, tipo_origen)
            VALUES (?, ?, ?, ?, ?, ?, 'costo')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Base"],
            p["Subtotal"], p["Item Disc. %"]
        ))

    conn.commit()
    conn.close()
    return cotizacion_id

class CotizacionPDFConLogo(FPDF):
    def header(self):
        self.image("LOGO Syn Apps Sys_edited (2).png", x=10, y=8, w=50)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(70, 12)
        self.cell(0, 10, "Cotización de Servicios", ln=True, align="L")
        self.ln(20)

    def encabezado_cliente(self, datos):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, f"Cliente: {datos['cliente']}", ln=True)
        self.cell(0, 8, f"Contacto: {datos['contacto']}", ln=True)
        self.cell(0, 8, f"Propuesta: {datos['propuesta']}", ln=True)
        self.cell(0, 8, f"Fecha: {datos['fecha']}", ln=True)
        self.cell(0, 8, f"Responsable: {datos['responsable']}", ln=True)
        self.ln(5)

    def tabla_productos(self, productos):
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 8, "Producto", 1)
        self.cell(20, 8, "Cantidad", 1, align="C")
        self.cell(30, 8, "P. Unitario", 1, align="R")
        self.cell(30, 8, "Descuento %", 1, align="R")
        self.cell(40, 8, "Total", 1, ln=True, align="R")

        self.set_font("Helvetica", "", 10)
        for p in productos:
            self.cell(60, 8, str(p["producto"]), 1)
            self.cell(20, 8, str(p["cantidad"]), 1, align="C")
            self.cell(30, 8, f"${p['precio_unitario']:,.2f}", 1, align="R")
            self.cell(30, 8, f"{p['descuento_aplicado']}%", 1, align="R")
            self.cell(40, 8, f"${p['precio_total']:,.2f}", 1, ln=True, align="R")
        self.ln(5)

    def totales(self, total_venta):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Total de la propuesta: ${total_venta:,.2f}", ln=True, align="R")
        self.ln(10)

    def condiciones(self):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 6,
            "Vigencia de la propuesta: 30 días naturales.
"
            "Precios en USD, no incluyen IVA.
"
            "Condiciones de pago: 50% anticipo, 50% contra entrega.
"
        )
        self.ln(10)

    def firma(self, responsable, cargo):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, "Atentamente,", ln=True)
        self.cell(0, 8, responsable, ln=True)
        if cargo:
            self.cell(0, 8, cargo, ln=True)

inicializar_db()
