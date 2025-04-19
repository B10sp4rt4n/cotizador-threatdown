
import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
from datetime import date
import os
import io

# ========================
# Configuración inicial
# ========================
st.set_page_config(page_title="Cotizador ThreatDown", layout="wide")

# ========================
# Funciones auxiliares de usuario
# ========================
DB_USUARIOS = "usuarios.sqlite"

def verificar_usuario(usuario, password):
    try:
        conn = sqlite3.connect(DB_USUARIOS)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash, rol FROM usuarios WHERE usuario = ?", (usuario,))
        resultado = cursor.fetchone()
        conn.close()
        if resultado and bcrypt.checkpw(password.encode(), resultado[0]):
            return True, resultado[1]
        return False, None
    except Exception as e:
        st.error(f"Error al verificar usuario: {e}")
        return False, None

# ========================
# Pantalla de login
# ========================
if "logueado" not in st.session_state:
    st.session_state.logueado = False
    st.session_state.usuario = ""
    st.session_state.rol = ""

if not st.session_state.logueado:
    st.title("Inicio de sesión")
    usuario = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Ingresar"):
        valido, rol = verificar_usuario(usuario, password)
        if valido:
            st.session_state.logueado = True
            st.session_state.usuario = usuario
            st.session_state.rol = rol
            st.success(f"Bienvenido {usuario} ({rol})")
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()

# ========================
# Lógica principal cotizador (idéntica al original)
# ========================
st.title("Cotizador ThreatDown con CRM")

for key in ["df_tabla_descuento", "df_cotizacion", "cliente", "contacto", "propuesta", "fecha", "responsable"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "fecha" else date.today()

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
        INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["total_venta"], datos["total_costo"],
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

@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()
inicializar_db()

# Aquí seguiría el mismo código exacto que ya tienes de inputs, selección, cálculos, etc.
st.info("🎉 El usuario está autenticado. Continúa con la cotización como siempre.")

