import os
import subprocess
import pandas as pd
import streamlit as st
import requests
from io import BytesIO

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
        st.error("No se pudo descargar el archivo Excel. Verifica la URL.")
        return None

df = load_data()

if df is not None:
    st.write("Archivo cargado correctamente")

    # Lista de productos permitidos
    productos_permitidos = [
        "ThreatDown ADVANCED", "ThreatDown ADVANCED SERVER", "ThreatDown CORE", "ThreatDown CORE SERVER",
        "ThreatDown ELITE", "ThreatDown ELITE SERVER", "ThreatDown MOBILE SECURITY", "ThreatDown ULTIMATE",
        "ThreatDown ULTIMATE SERVER"
    ]

    # Limpiar nombres de productos
    df["Product Title"] = df["Product Title"].astype(str).str.replace("\n", " ", regex=True).str.strip()

    # Filtrar solo los productos permitidos
    df_filtrado = df[df["Product Title"].isin(productos_permitidos)]

    # Interfaz de usuario con Streamlit
    st.write("Selecciona los productos para la cotización:")

    cotizacion = []
    for i in range(6):  # Máximo 6 productos
        producto = st.selectbox(f"Producto {i+1}", ["Selecciona..."] + productos_permitidos, key=f"producto_{i}")
        if producto != "Selecciona...":
            cantidad = st.number_input(f"Cantidad de {producto}", min_value=1, step=1, key=f"cantidad_{i}")
            margen = st.number_input(f"Margen (%) para {producto}", min_value=0.0, max_value=100.0, step=0.1, key=f"margen_{i}")
            precio_lista = df_filtrado[df_filtrado["Product Title"] == producto]["MSRP USD"].values[0]
            precio_final_unitario = precio_lista * (1 + margen / 100)
            precio_total = precio_final_unitario * cantidad
            cotizacion.append([producto, cantidad, precio_lista, precio_final_unitario, precio_total])
        else:
            break

    if cotizacion:
        df_cotizacion = pd.DataFrame(cotizacion, columns=["Producto", "Cantidad", "Precio Lista Unitario", "Precio Final Unitario", "Precio Total"])
        st.write("Cotización generada:")
        st.dataframe(df_cotizacion)
    else:
        st.warning("No has seleccionado ningún producto para cotizar.")
else:
    st.error("No se pudo cargar el archivo Excel.")
