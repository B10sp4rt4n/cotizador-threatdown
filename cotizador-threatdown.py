import streamlit as st
import pandas as pd

# Cargar precios desde el archivo Excel
@st.cache_data
def cargar_datos():
    return pd.read_excel("precios_threatdown.xlsx")

df_precios = cargar_datos()

st.title("Cotizador ThreatDown")

# Mostrar productos disponibles
productos = df_precios["Product Title"].unique()
seleccion = st.multiselect("Selecciona los productos que deseas cotizar:", productos)

# Mostrar precios y permitir elegir cantidades
cotizacion = []
for prod in seleccion:
    fila = df_precios[df_precios["Product Title"] == prod].iloc[0]
    precio_unitario = fila["MSRP USD"]
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
