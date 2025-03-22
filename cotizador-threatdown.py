# cotizador_threatdown.py

import streamlit as st
import pandas as pd

# Cargar precios desde el archivo Excel
@st.cache_data
def cargar_datos():
    return pd.read_excel("precios_threatdown.xlsx")

df_precios = cargar_datos()

st.title("Cotizador ThreatDown")

# Mostrar productos disponibles
productos = df_precios["Producto"].unique()
seleccion = st.multiselect("Selecciona los productos que deseas cotizar:", productos)

# Mostrar precios y permitir elegir cantidades
cotizacion = []
for prod in seleccion:
    precio_unitario = df_precios[df_precios["Producto"] == prod]["Precio Unitario"].values[0]
    cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1, step=1)
    subtotal = precio_unitario * cantidad
    cotizacion.append({
        "Producto": prod,
        "Cantidad": cantidad,
        "Precio Unitario": precio_unitario,
        "Subtotal": subtotal
    })

# Mostrar desglose
if cotizacion:
    df_cotizacion = pd.DataFrame(cotizacion)
    st.subheader("Resumen de Cotización")
    st.dataframe(df_cotizacion)
    total = df_cotizacion["Subtotal"].sum()
    st.success(f"Total: ${total:,.2f}")

# (Opcional) Botón para exportar a Excel o PDF más adelante


