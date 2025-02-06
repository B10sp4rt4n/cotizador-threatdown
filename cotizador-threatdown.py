import os
import subprocess
import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from fpdf import FPDF

# Asegurar que openpyxl esté instalado
try:
    import openpyxl
except ImportError:
    subprocess.run(["pip", "install", "openpyxl"])
    import openpyxl

st.title("Cotizador ThreatDown")

# URL del archivo Excel en GitHub (versión RAW)
url_excel = "https://raw.githubusercontent.com/B10sp4rt4n/cotizador-threatdown/main/Lista%20de%20Precios%20ThD.xlsx"

# Cargar datos desde el archivo Excel
@st.cache_data
def load_data():
    response = requests.get(url_excel)
    if response.status_code == 200:
        return pd.read_excel(BytesIO(response.content), sheet_name="Table003 (Page 21-64)")
    else:
        return None

df = load_data()

if df is None:
    st.error("No se pudo cargar el archivo Excel.")
else:
    st.write("Archivo cargado correctamente")

    # Extraer información de SKU
    def extraer_info_sku(sku, rango_texto):
        partes = sku.split("B")
        if len(partes) < 2:
            return None, (1, 1), None
        
        contrato_meses = int(partes[0][-2:]) if partes[0][-2:].isdigit() else None
        tipo_licencia = "SERVER" if "SERVER" in sku else "NORMAL"
        
        # Extraer el rango de licencias desde el texto con manejo de errores
        try:
            if isinstance(rango_texto, str) and "-" in rango_texto:
                rango_min, rango_max = map(int, rango_texto.replace("License Range:", "").strip().split("-"))
            else:
                rango_min, rango_max = 1, 1
        except ValueError:
            rango_min, rango_max = 1, 1
        
        return contrato_meses, (rango_min, rango_max), tipo_licencia
    
    df["Contrato (Meses)"], df["Rango"], df["Tipo de Licencia"] = zip(*df.apply(lambda row: extraer_info_sku(str(row.get("Product Number", "")), str(row.get("License Range", ""))), axis=1))
    df["Rango Min"] = df["Rango"].apply(lambda x: x[0])  # Extraer rango mínimo para ordenar
    
    # Filtrar productos permitidos y excluir Non-Commercial
    productos_permitidos = [
        "ThreatDown ADVANCED", "ThreatDown ADVANCED SERVER", "ThreatDown CORE", "ThreatDown CORE SERVER",
        "ThreatDown ELITE", "ThreatDown ELITE SERVER", "ThreatDown MOBILE SECURITY", "ThreatDown ULTIMATE",
        "ThreatDown ULTIMATE SERVER"
    ]
    
    df["Product Title"] = df["Product Title"].astype(str).str.replace("\n", " ", regex=True).str.strip()
    df_filtrado = df[df["Product Title"].isin(productos_permitidos)]
    
    # Excluir Non-Commercial de la columna E si existe
    if "E" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["E"].astype(str).str.contains("Business", case=False, na=False)]
    
    # Interfaz de usuario con Streamlit
    st.write("Selecciona los productos para la cotización:")

    cotizacion = []
    consecutivo = 1

    while True:
        producto = st.selectbox(f"Producto {consecutivo}", ["Selecciona..."] + productos_permitidos, key=f"producto_{consecutivo}_{st.session_state.get('session_id', 0)}")
        if producto != "Selecciona...":
            contrato_meses = st.selectbox(f"Tiempo de contratación para {producto}", [12, 24, 36], key=f"contrato_{consecutivo}_{st.session_state.get('session_id', 0)}")
            cantidad = st.number_input(f"Cantidad de {producto}", min_value=1, step=1, key=f"cantidad_{consecutivo}_{st.session_state.get('session_id', 0)}")
            descuento = st.number_input(f"Descuento (%) para {producto}", min_value=0.0, max_value=100.0, step=0.1, key=f"descuento_{consecutivo}_{st.session_state.get('session_id', 0)}")
            
            # Filtrar según los criterios seleccionados y el rango correcto
            df_seleccion = df_filtrado[(df_filtrado["Product Title"] == producto) & (df_filtrado["Contrato (Meses)"] == contrato_meses)]
            df_seleccion = df_seleccion[df_seleccion["Rango"].apply(lambda r: r[0] <= cantidad <= r[1])]
            
            # Verificar si la columna Rango Min está presente en df_seleccion antes de ordenar
            if "Rango Min" not in df_seleccion.columns:
                df_seleccion["Rango Min"] = df_seleccion["Rango"].apply(lambda x: x[0])
            
            df_seleccion = df_seleccion.sort_values(by=["Rango Min"])  # Ordenar por rango mínimo correctamente
            
            if not df_seleccion.empty:
                precio_lista = df_seleccion.iloc[0]["MSRP USD"]
                precio_final_unitario = precio_lista * (1 - descuento / 100)
                precio_total = precio_final_unitario * cantidad
                cotizacion.append([consecutivo, producto, contrato_meses, cantidad, precio_lista, precio_final_unitario, precio_total])
            else:
                st.warning(f"No se encontró una opción válida para {producto} con {contrato_meses} meses y cantidad {cantidad}.")
            
            agregar_otro = st.radio("¿Deseas agregar otro producto?", ["Sí", "No"], key=f"continuar_{consecutivo}_{st.session_state.get('session_id', 0)}")
            if agregar_otro == "No" or consecutivo == 6:
                break
            consecutivo += 1
        else:
            break


