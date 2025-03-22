
import streamlit as st
import pandas as pd

# Cargar precios desde el archivo Excel
@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    # Convertir Tier Min y Tier Max a números, forzar errores a NaN y eliminar filas inválidas
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    df = df.dropna(subset=["Tier Min", "Tier Max"])
    return df

df_precios = cargar_datos()

st.title("Cotizador ThreatDown")

# Filtro 1: Selección del término (12, 24, 36 meses)
terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (en meses):", terminos_disponibles)

# Filtrar el DataFrame por el término seleccionado
df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado]

# Mostrar productos disponibles con ese término
productos = df_filtrado_termino["Product Title"].unique()
seleccion = st.multiselect("Selecciona los productos que deseas cotizar:", productos)

# Mostrar precios y permitir elegir cantidades
cotizacion = []
for prod in seleccion:
    # Obtener solo las filas del producto seleccionado y término correcto
    df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod]

    cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1, step=1)

    # Filtrar por rango de Tier Min y Max
    df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]

    if not df_rango.empty:
        fila = df_rango.iloc[0]
        precio_unitario = fila["MSRP USD"]
        subtotal = precio_unitario * cantidad
        cotizacion.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Unitario": precio_unitario,
            "Subtotal": subtotal
        })
    else:
        st.warning(f"No hay precios disponibles para '{prod}' con cantidad {cantidad}.")

# Mostrar desglose
if cotizacion:
    df_cotizacion = pd.DataFrame(cotizacion)
    st.subheader("Resumen de Cotización")
    st.dataframe(df_cotizacion)
    total = df_cotizacion["Subtotal"].sum()
    st.success(f"Total: ${total:,.2f}")
