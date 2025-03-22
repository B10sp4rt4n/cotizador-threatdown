
import streamlit as st
import pandas as pd

# Cargar precios desde el archivo Excel
@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    df = df.dropna(subset=["Tier Min", "Tier Max"])
    return df

df_precios = cargar_datos()

st.title("Cotizador ThreatDown con Descuentos")

# Filtro 1: Selección del término (12, 24, 36 meses)
terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (en meses):", terminos_disponibles)

# Filtrar el DataFrame por el término seleccionado
df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado]

# Mostrar productos disponibles con ese término
productos = df_filtrado_termino["Product Title"].unique()
seleccion = st.multiselect("Selecciona los productos que deseas cotizar:", productos)

# Mostrar precios y permitir elegir cantidades y descuentos
cotizacion = []
for prod in seleccion:
    df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod]
    cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1, step=1)

    df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]

    if not df_rango.empty:
        fila = df_rango.iloc[0]
        precio_base = fila["MSRP USD"]

        # Descuentos personalizados por producto
        item_disc = st.number_input(f"Descuento 'Item' (%) para '{prod}':", min_value=0.0, max_value=100.0, value=0.0)
        channel_disc = st.number_input(f"Descuento 'Channel Disc.' (%) para '{prod}':", min_value=0.0, max_value=100.0, value=0.0)
        deal_reg_disc = st.number_input(f"Descuento 'Deal Reg. Disc.' (%) para '{prod}':", min_value=0.0, max_value=100.0, value=0.0)

        # Aplicar descuentos
        precio1 = precio_base * (1 - item_disc / 100)
        total_channel = channel_disc + deal_reg_disc
        precio_final = precio1 * (1 - total_channel / 100)

        subtotal = precio_final * cantidad

        cotizacion.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Base": precio_base,
            "Item Disc. %": item_disc,
            "Channel + Deal Disc. %": total_channel,
            "Precio Final Unitario": round(precio_final, 2),
            "Subtotal": round(subtotal, 2)
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


