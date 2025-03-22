
import streamlit as st
import pandas as pd

# Cargar precios desde el archivo Excel
@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

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
productos_para_tabla_secundaria = []

for prod in seleccion:
    df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod]
    cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1, step=1)

    df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]

    if not df_rango.empty:
        fila = df_rango.iloc[0]
        precio_base = fila["MSRP USD"]

        # Descuentos personalizados por producto (cotización base)
        item_disc = st.number_input(f"Descuento 'Item' (%) para '{prod}':", min_value=0.0, max_value=100.0, value=0.0)
        channel_disc = st.number_input(f"Descuento 'Channel Disc.' (%) para '{prod}':", min_value=0.0, max_value=100.0, value=0.0)
        deal_reg_disc = st.number_input(f"Descuento 'Deal Reg. Disc.' (%) para '{prod}':", min_value=0.0, max_value=100.0, value=0.0)

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

        productos_para_tabla_secundaria.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Unitario de Lista": precio_base
        })
    else:
        st.warning(f"No hay precios disponibles para '{prod}' con cantidad {cantidad}.")

# Mostrar desglose original con descuentos en cascada
costo_total = 0
if cotizacion:
    df_cotizacion = pd.DataFrame(cotizacion)
    st.subheader("Resumen de Cotización (costo con descuentos en cascada)")
    st.dataframe(df_cotizacion)
    costo_total = df_cotizacion["Subtotal"].sum()
    st.success(f"Costo total con descuentos aplicados: ${costo_total:,.2f}")

# NUEVA TABLA INDEPENDIENTE AL FINAL
st.subheader("Análisis independiente: Precio de venta con descuento directo sobre precio de lista")

precio_venta_total = 0
if productos_para_tabla_secundaria:
    tabla_descuento = []
    for item in productos_para_tabla_secundaria:
        prod = item["Producto"]
        cantidad = item["Cantidad"]
        precio_unitario = item["Precio Unitario de Lista"]
        precio_total_lista = precio_unitario * cantidad

        descuento_directo = st.number_input(f"Descuento directo (%) sobre lista para '{prod}':",
                                            min_value=0.0, max_value=100.0, value=0.0,
                                            key=f"direct_discount_{prod}")
        precio_con_descuento = precio_total_lista * (1 - descuento_directo / 100)

        tabla_descuento.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Unitario de Lista": round(precio_unitario, 2),
            "Precio Total de Lista": round(precio_total_lista, 2),
            "Descuento %": descuento_directo,
            "Precio Total con Descuento": round(precio_con_descuento, 2)
        })

    df_tabla_descuento = pd.DataFrame(tabla_descuento)
    st.dataframe(df_tabla_descuento)
    precio_venta_total = df_tabla_descuento["Precio Total con Descuento"].sum()
    st.success(f"Precio de venta total (descuento directo aplicado): ${precio_venta_total:,.2f}")
else:
    st.info("Aún no hay productos con precios de lista válidos para aplicar descuento directo.")

# Cálculo de utilidad y margen (CORRECTO)
if precio_venta_total > 0 and costo_total > 0:
    utilidad = precio_venta_total - costo_total
    margen = (utilidad / precio_venta_total) * 100
    st.subheader("Utilidad de la operación")
    col1, col2 = st.columns(2)
    col1.metric("Utilidad total", f"${utilidad:,.2f}")
    col2.metric("Margen (%)", f"{margen:.2f}%")


