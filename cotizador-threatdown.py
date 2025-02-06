import pandas as pd
import streamlit as st

# Cargar el archivo con productos filtrados
file_path = "/mnt/data/Lista de Precios ThD.xlsx"
df = pd.read_excel(file_path, sheet_name="Table003 (Page 21-64)")

# Lista de productos permitidos
productos_permitidos = [
    "ThreatDown ADVANCED", "ThreatDown ADVANCED SERVER", "ThreatDown CORE", "ThreatDown CORE SERVER",
    "ThreatDown ELITE", "ThreatDown ELITE SERVER", "ThreatDown MOBILE SECURITY", "ThreatDown ULTIMATE",
    "ThreatDown ULTIMATE SERVER"
]

# Limpiar nombres de productos
df["Product Title"] = df["Product Title"].str.replace("\n", " ", regex=True).str.strip()

# Filtrar productos
df_filtrado = df[df["Product Title"].isin(productos_permitidos)]

# Interfaz de usuario con Streamlit
st.title("Cotizador ThreatDown")

productos_seleccionados = []

# Agregar productos hasta un máximo de 6
for i in range(6):
    producto = st.selectbox(f"Selecciona el producto {i+1}", ["Selecciona..."] + productos_permitidos, key=f"producto_{i}")
    if producto != "Selecciona...":
        productos_seleccionados.append(producto)
    else:
        break

# Filtrar los productos seleccionados
df_cotizacion = df_filtrado[df_filtrado["Product Title"].isin(productos_seleccionados)]

if not df_cotizacion.empty:
    st.write("Cotización generada:")
    st.dataframe(df_cotizacion)
else:
    st.write("No se han seleccionado productos para cotizar.")
