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
# Funciones de base de datos (optimizadas)
# ========================
def inicializar_db():
    """Crea la estructura inicial de la base de datos con verificación segura de columnas"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Tabla principal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, contacto TEXT, propuesta TEXT,
                fecha TEXT, responsable TEXT, total_venta REAL,
                total_costo REAL, utilidad REAL, margen REAL,
                vigencia TEXT, condiciones_comerciales TEXT
            )""")
        
        # Tabla detalle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER, producto TEXT, cantidad INTEGER,
                precio_unitario REAL, precio_total REAL,
                descuento_aplicado REAL, tipo_origen TEXT,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
            )""")
        
        # Verificación segura de columnas
        columnas_existentes = [col[1] for col in 
                             cursor.execute("PRAGMA table_info(cotizaciones)").fetchall()]
        for col in ["vigencia", "condiciones_comerciales"]:
            if col not in columnas_existentes:
                cursor.execute(f"ALTER TABLE cotizaciones ADD COLUMN {col} TEXT;")

def conectar_db():
    return sqlite3.connect(DB_PATH)

def guardar_cotizacion(datos, productos_venta, productos_costo):
    """Guarda toda la información de la cotización de forma transaccional"""
    with conectar_db() as conn:
        cursor = conn.cursor()
        
        # Insertar cabecera
        cursor.execute("""
            INSERT INTO cotizaciones (
                cliente, contacto, propuesta, fecha, responsable,
                total_venta, total_costo, utilidad, margen,
                vigencia, condiciones_comerciales
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            tuple(datos.values()))
        
        cotizacion_id = cursor.lastrowid
        
        # Insertar detalles
        for tipo, productos in [('venta', productos_venta), ('costo', productos_costo)]:
            for p in productos:
                cursor.execute("""
                    INSERT INTO detalle_productos (
                        cotizacion_id, producto, cantidad, precio_unitario,
                        precio_total, descuento_aplicado, tipo_origen
                    ) VALUES (?,?,?,?,?,?,?)""",
                    (cotizacion_id, p["Producto"], p["Cantidad"],
                     p.get("Precio Unitario de Lista", p.get("Precio Base")),
                     p["Precio Total con Descuento"] if tipo == 'venta' else p["Subtotal"],
                     p["Descuento %"] if tipo == 'venta' else p["Item Disc. %"],
                     tipo))
        
        return cotizacion_id

# ========================
# Componentes reutilizables
# ========================
def mostrar_encabezado():
    st.title("Cotizador ThreatDown con CRM")
    with st.sidebar:
        st.header("Datos de la cotización")
        return {
            "cliente": st.text_input("Cliente"),
            "contacto": st.text_input("Nombre de contacto"),
            "propuesta": st.text_input("Nombre de la propuesta"),
            "fecha": st.date_input("Fecha", value=date.today()),
            "responsable": st.text_input("Responsable / Vendedor")
        }

def mostrar_condiciones():
    col1, col2 = st.columns(2)
    with col1:
        vigencia = st.text_input("Vigencia de la propuesta", value="30 días")
    with col2:
        condiciones = st.text_area(
            "Condiciones Comerciales",
            value="Precios en USD. Pago contra entrega. No incluye impuestos.",
            height=100
        )
    return vigencia, condiciones

# ========================
# Lógica principal optimizada
# ========================
def main():
    # Configuración inicial
    inicializar_db()
    datos_cliente = mostrar_encabezado()
    vigencia, condiciones = mostrar_condiciones()
    
    # Carga de precios
    df_precios = cargar_datos()  # Mantenemos misma función de carga
    
    # Selección de productos y cálculo de costos
    termino = st.selectbox(
        "Selecciona el plazo del servicio (en meses):",
        options=sorted(df_precios["Term (Month)"].dropna().unique())
    )
    
    df_filtrado = df_precios[df_precios["Term (Month)"] == termino]
    productos_seleccionados = st.multiselect(
        "Selecciona los productos:",
        df_filtrado["Product Title"].unique()
    )
    
    # Procesamiento de productos
    costos, ventas = procesar_productos(df_filtrado, productos_seleccionados)
    
    # Mostrar resultados y guardar
    if costos and ventas:
        mostrar_resultados(costos, ventas, datos_cliente, vigencia, condiciones)
        mostrar_historial()

# ========================
# Funciones de procesamiento
# ========================
def procesar_productos(df_filtrado, productos_seleccionados):
    costos = []
    ventas = []
    
    for prod in productos_seleccionados:
        df_producto = df_filtrado[df_filtrado["Product Title"] == prod]
        cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1)
        
        # Validación de rango de cantidad
        rango_valido = df_producto[
            (df_producto["Tier Min"] <= cantidad) & 
            (df_producto["Tier Max"] >= cantidad)
        ]
        
        if rango_valido.empty:
            st.warning(f"Rango no válido para {prod} con cantidad {cantidad}")
            continue
            
        precio_base = rango_valido.iloc[0]["MSRP USD"]
        
        # Cálculo de descuentos
        item_disc, channel_disc, deal_disc = obtener_descuentos(prod)
        precio_final = calcular_precio_final(precio_base, item_disc, channel_disc, deal_disc)
        
        # Construcción de registros
        costos.append({
            "Producto": prod, "Cantidad": cantidad, "Precio Base": precio_base,
            "Item Disc. %": item_disc, "Subtotal": round(precio_final * cantidad, 2)
        })
        
        ventas.append({
            "Producto": prod, "Cantidad": cantidad,
            "Precio Unitario de Lista": precio_base,
            "Descuento %": item_disc + channel_disc + deal_disc,
            "Precio Total con Descuento": round(precio_final * cantidad, 2)
        })
    
    return costos, ventas

def obtener_descuentos(producto):
    """Muestra inputs de descuentos en columnas"""
    cols = st.columns(3)
    with cols[0]: item = st.number_input(f"Item Disc (%) - {producto}", 0.0, 100.0, 0.0)
    with cols[1]: channel = st.number_input(f"Channel Disc (%) - {producto}", 0.0, 100.0, 0.0)
    with cols[2]: deal = st.number_input(f"Deal Reg Disc (%) - {producto}", 0.0, 100.0, 0.0)
    return item, channel, deal

def calcular_precio_final(base, item, channel, deal):
    """Aplica descuentos en cascada"""
    return base * (1 - item/100) * (1 - (channel + deal)/100)

# Resto del código manteniendo la estructura original pero optimizado...
# (Generación de PDF, visualización de historial, cálculos de utilidad, etc.)

if __name__ == "__main__":
    main()
