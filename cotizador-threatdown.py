import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
from fpdf import FPDF

# ========================
# Configuración inicial
# ========================
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")
LOGO_PATH = "LOGO Syn Apps Sys_edited (2).png"

# ========================
# Funciones de base de datos
# ========================
def inicializar_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, contacto TEXT, propuesta TEXT,
                fecha TEXT, responsable TEXT, 
                total_lista REAL, total_costo REAL, total_venta REAL,
                utilidad REAL, margen REAL,
                vigencia TEXT, condiciones_comerciales TEXT
            )""")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER, producto TEXT, cantidad INTEGER,
                precio_lista REAL, descuento_costo REAL, costo REAL,
                descuento_venta REAL, precio_venta REAL,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
            )""")

def conectar_db():
    return sqlite3.connect(DB_PATH)

# ========================
# Funciones de carga de datos
# ========================
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_excel("precios_threatdown.xlsx")
        df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
        df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
        return df.dropna(subset=["Tier Min", "Tier Max"])
    except FileNotFoundError:
        st.error("❌ Archivo 'precios_threatdown.xlsx' no encontrado")
        st.stop()
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        st.stop()

# ========================
# Componentes de la interfaz
# ========================
def mostrar_encabezado():
    st.title("🛒 Cotizador ThreatDown Professional")
    with st.sidebar:
        st.header("📋 Datos Comerciales")
        return {
            "cliente": st.text_input("Cliente"),
            "contacto": st.text_input("Contacto"),
            "propuesta": st.text_input("Propuesta"),
            "fecha": st.date_input("Fecha", value=date.today()),
            "responsable": st.text_input("Responsable"),
            "vigencia": st.text_input("Vigencia", value="30 días"),
            "condiciones_comerciales": st.text_area(
                "Condiciones Comerciales", 
                value="Precios en USD. Pago contra entrega."
            )
        }

# ========================
# Generador de PDF
# ========================
class CotizacionPDF(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=40)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Cliente: {self.cliente}", ln=True)
        self.cell(0, 10, f"Contacto: {self.contacto}", ln=True)
        self.cell(0, 10, f"Propuesta: {self.propuesta}", ln=True)
        self.cell(0, 10, f"Vigencia: {self.vigencia}", ln=True)
        self.ln(10)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Cotización Comercial", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-40)
        self.set_font("Helvetica", "I", 10)
        self.multi_cell(0, 5, f"Condiciones Comerciales:\n{self.condiciones}")
        self.ln(5)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Responsable: {self.responsable}", ln=True)
        if os.path.exists("firma_synappssys.png"):
            self.image("firma_synappssys.png", x=50, y=self.get_y(), w=100)
        self.cell(0, 10, "SynAppsSys", 0, 0, "C")

    def tabla_productos(self, data):
        self.set_font("Helvetica", "B", 10)
        headers = ["Cantidad", "Producto", "Periodo", "P. Unitario", "P. Lista", "Descuento %", "P. Final"]
        col_widths = [20, 60, 20, 30, 30, 30, 30]
        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, 1, 0, "C")
        self.ln()

        self.set_font("Helvetica", "", 10)
        total = 0
        for item in data:
            self.cell(col_widths[0], 10, str(item["cantidad"]), 1, 0, "C")
            self.cell(col_widths[1], 10, item["producto"], 1)
            self.cell(col_widths[2], 10, f"{self.periodo} meses", 1, 0, "C")
            self.cell(col_widths[3], 10, f"${item['precio_venta']:.2f}", 1, 0, "R")
            self.cell(col_widths[4], 10, f"${item['precio_lista']:.2f}", 1, 0, "R")
            self.cell(col_widths[5], 10, f"{item['descuento_venta']:.1f}%", 1, 0, "C")
            self.cell(col_widths[6], 10, f"${item['total_venta']:.2f}", 1, 0, "R")
            self.ln()
            total += item["total_venta"]

        self.set_font("Helvetica", "B", 10)
        self.cell(sum(col_widths[:-1]), 10, "TOTAL:", 1, 0, "R")
        self.cell(col_widths[-1], 10, f"${total:.2f}", 1, 0, "R")

# ========================
# Lógica principal
# ========================
# (En el procesamiento de productos, aplicar lógica secuencial de descuentos: primero Item Disc, luego Channel Disc, luego Deal Reg Disc)
