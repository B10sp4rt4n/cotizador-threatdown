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
        return None

df = load_data()

if df is None:
    st.error("No se pudo cargar el archivo Excel.")
else:
    st.write("Archivo cargado correctamente")

    # Extraer información de SKU
    def extraer_info_sku(sku):
        partes = sku.split("B")
        if len(partes) < 2:
            return None, None, None
        
        contrato_meses = int(partes[0][-2:]) if partes[0][-2:].isdigit() else None
        rango = int(partes[1]) if partes[1].isdigit() else None
        tipo_licencia = "SERVER" if "SERVER" in sku else "NORMAL"
        
        return contrato_meses, rango, tipo_licencia
    
    df["Contrato (Meses)"], df["Rango"], df["Tipo de Licencia"] = zip(*df["Product Number"].apply(extraer_info_sku))
    
    # Filtrar productos permitidos
    productos_permitidos = [
        "ThreatDown ADVANCED", "ThreatDown ADVANCED SERVER", "ThreatDown CORE", "ThreatDown CORE SERVER",
        "ThreatDown ELITE", "ThreatDown ELITE SERVER", "ThreatDown MOBILE SECURITY", "ThreatDown ULTIMATE",
        "ThreatDown ULTIMATE SERVER"
    ]
    
    df["Product Title"] = df["Product Title"].astype(str).str.replace("\n", " ", regex=True).str.strip()
    df_filtrado = df[df["Product Title"].isin(productos_permitidos)]
    
    # Interfaz de usuario con Streamlit
    st.write("Selecciona los productos para la cotización:")

    cotizacion = []
    consecutivo = 1

    while True:
        producto = st.selectbox(f"Producto {consecutivo}", ["Selecciona..."] + productos_permitidos, key=f"producto_{consecutivo}")
        if producto != "Selecciona...":
            contrato_meses = st.selectbox(f"Tiempo de contratación para {producto}", [12, 24, 36], key=f"contrato_{consecutivo}")
            cantidad = st.number_input(f"Cantidad de {producto}", min_value=1, step=1, key=f"cantidad_{consecutivo}")
            descuento = st.number_input(f"Descuento (%) para {producto}", min_value=0.0, max_value=100.0, step=0.1, key=f"descuento_{consecutivo}")
            
            # Filtrar según los criterios seleccionados y el rango
            df_seleccion = df_filtrado[(df_filtrado["Product Title"] == producto) & (df_filtrado["Contrato (Meses)"] == contrato_meses)]
            df_seleccion = df_seleccion[(df_seleccion["Rango"] >= cantidad) | (df_seleccion["Rango"] == 1)]
            df_seleccion = df_seleccion.sort_values(by=["Rango"])  # Ordenar para elegir el precio correcto
            
            if not df_seleccion.empty:
                precio_lista = df_seleccion.iloc[0]["MSRP USD"]
                precio_final_unitario = precio_lista * (1 - descuento / 100)
                precio_total = precio_final_unitario * cantidad
                cotizacion.append([consecutivo, producto, contrato_meses, cantidad, precio_lista, precio_final_unitario, precio_total])
            else:
                st.warning(f"No se encontró una opción válida para {producto} con {contrato_meses} meses y cantidad {cantidad}.")
            
            agregar_otro = st.radio("¿Deseas agregar otro producto?", ["Sí", "No"], key=f"continuar_{consecutivo}")
            if agregar_otro == "No" or consecutivo == 6:
                break
            consecutivo += 1
        else:
            break

    if cotizacion:
        df_cotizacion = pd.DataFrame(cotizacion, columns=["#", "Producto", "Contrato (Meses)", "Cantidad", "Precio Lista Unitario", "Precio Final Unitario", "Precio Total"])
        subtotal = df_cotizacion["Precio Total"].sum()
        iva = subtotal * 0.16
        gran_total = subtotal + iva
        
        st.write("Cotización generada:")
        st.dataframe(df_cotizacion)
        st.write(f"**Subtotal:** ${subtotal:,.2f}")
        st.write(f"**IVA (16%):** ${iva:,.2f}")
        st.write(f"**Gran Total:** ${gran_total:,.2f}")
    else:
        st.warning("No has seleccionado ningún producto para cotizar.")


