
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date

# Crear ruta segura para base de datos en entorno escribible
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")

# ========================
# Crear base y tablas si no existen
# ========================
def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cotizaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT,
            contacto TEXT,
            propuesta TEXT,
            fecha TEXT,
            responsable TEXT,
            total_venta REAL,
            total_costo REAL,
            utilidad REAL,
            margen REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detalle_productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cotizacion_id INTEGER,
            producto TEXT,
            cantidad INTEGER,
            precio_unitario REAL,
            precio_total REAL,
            descuento_aplicado REAL,
            tipo_origen TEXT,
            FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
        )
    """)
    conn.commit()
    conn.close()

def conectar_db():
    return sqlite3.connect(DB_PATH)

def guardar_cotizacion(datos, productos_venta, productos_costo):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["total_venta"], datos["total_costo"],
        datos["utilidad"], datos["margen"]
    ))
    cotizacion_id = cursor.lastrowid

    for p in productos_venta:
        cursor.execute("""
            INSERT INTO detalle_productos (cotizacion_id, producto, cantidad, precio_unitario, precio_total, descuento_aplicado, tipo_origen)
            VALUES (?, ?, ?, ?, ?, ?, 'venta')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Unitario de Lista"],
            p["Precio Total con Descuento"], p["Descuento %"]
        ))

    for p in productos_costo:
        cursor.execute("""
            INSERT INTO detalle_productos (cotizacion_id, producto, cantidad, precio_unitario, precio_total, descuento_aplicado, tipo_origen)
            VALUES (?, ?, ?, ?, ?, ?, 'costo')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Base"],
            p["Subtotal"], p["Item Disc. %"]
        ))

    conn.commit()
    conn.close()
    return cotizacion_id

def ver_historial():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM cotizaciones ORDER BY fecha DESC", conn)
    conn.close()
    return df

# Inicializar base si es primera vez
inicializar_db()

@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()

st.title("Cotizador ThreatDown con CRM")

st.sidebar.header("Datos de la cotización")
cliente = st.sidebar.text_input("Cliente")
contacto = st.sidebar.text_input("Nombre de contacto")
propuesta = st.sidebar.text_input("Nombre de la propuesta")
fecha = st.sidebar.date_input("Fecha", value=date.today())
responsable = st.sidebar.text_input("Responsable / Vendedor")

terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (en meses):", terminos_disponibles)

df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado]
productos = df_filtrado_termino["Product Title"].unique()
seleccion = st.multiselect("Selecciona los productos que deseas cotizar:", productos)

cotizacion = []
productos_para_tabla_secundaria = []

for prod in seleccion:
    df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod]
    cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1, step=1)

    df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]
    if not df_rango.empty:
        fila = df_rango.iloc[0]
        precio_base = fila["MSRP USD"]

        item_disc = st.number_input(f"Descuento 'Item' (%) para '{prod}':", 0.0, 100.0, 0.0)
        channel_disc = st.number_input(f"Descuento 'Channel Disc.' (%) para '{prod}':", 0.0, 100.0, 0.0)
        deal_reg_disc = st.number_input(f"Descuento 'Deal Reg. Disc.' (%) para '{prod}':", 0.0, 100.0, 0.0)

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

if cliente or propuesta or responsable:
    st.subheader("Datos de la cotización")
    st.markdown(f"**Cliente:** {cliente}")
    st.markdown(f"**Contacto:** {contacto}")
    st.markdown(f"**Propuesta:** {propuesta}")
    st.markdown(f"**Fecha:** {fecha.strftime('%Y-%m-%d')}")
    st.markdown(f"**Responsable:** {responsable}")

costo_total = 0
if cotizacion:
    df_cotizacion = pd.DataFrame(cotizacion)
    st.subheader("Resumen de Cotización (costos)")
    st.dataframe(df_cotizacion)
    costo_total = df_cotizacion["Subtotal"].sum()
    st.success(f"Costo total con descuentos aplicados: ${costo_total:,.2f}")

precio_venta_total = 0
tabla_descuento = []
if productos_para_tabla_secundaria:
    st.subheader("Análisis: Precio de venta con descuento directo sobre lista")
    for item in productos_para_tabla_secundaria:
        prod = item["Producto"]
        cantidad = item["Cantidad"]
        precio_unitario = item["Precio Unitario de Lista"]
        precio_total_lista = precio_unitario * cantidad

        descuento_directo = st.number_input(f"Descuento directo (%) sobre lista para '{prod}':",
                                            0.0, 100.0, 0.0, key=f"direct_discount_{prod}")
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
    st.success(f"Precio total de venta: ${precio_venta_total:,.2f}")
else:
    st.info("Aún no hay productos válidos para aplicar descuento directo.")

if precio_venta_total > 0 and costo_total > 0:
    utilidad = precio_venta_total - costo_total
    margen = (utilidad / precio_venta_total) * 100
    st.subheader("Utilidad de la operación")
    col1, col2 = st.columns(2)
    col1.metric("Utilidad total", f"${utilidad:,.2f}")
    col2.metric("Margen (%)", f"{margen:.2f}%")

    if st.button("💾 Guardar cotización"):
        datos = {
            "cliente": cliente,
            "contacto": contacto,
            "propuesta": propuesta,
            "fecha": fecha.strftime('%Y-%m-%d'),
            "responsable": responsable,
            "total_venta": precio_venta_total,
            "total_costo": costo_total,
            "utilidad": utilidad,
            "margen": margen
        }
        guardar_cotizacion(datos, df_tabla_descuento.to_dict("records"), df_cotizacion.to_dict("records"))
        st.success("✅ Cotización guardada en CRM")

st.subheader("📋 Historial de cotizaciones")
try:
    df_hist = ver_historial()
    st.dataframe(df_hist)
except:
    st.warning("No hay cotizaciones guardadas aún.")



# Vista detallada de cotización
st.subheader("🔍 Ver detalle de cotización guardada")
try:
    df_hist = ver_historial()

    if not df_hist.empty:
        opciones = df_hist.apply(lambda row: f"{row['id']} - {row['propuesta']} ({row['cliente']})", axis=1)
        seleccion_detalle = st.selectbox("Selecciona una cotización para ver el detalle:", opciones)

        if seleccion_detalle:
            id_seleccionado = int(seleccion_detalle.split(" - ")[0])
            conn = conectar_db()
            detalle = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {id_seleccionado}", conn)
            productos = pd.read_sql_query(f"SELECT * FROM detalle_productos WHERE cotizacion_id = {id_seleccionado}", conn)
            conn.close()

            cotiz = detalle.iloc[0]
            st.markdown(f"**Cliente:** {cotiz['cliente']}")
            st.markdown(f"**Contacto:** {cotiz['contacto']}")
            st.markdown(f"**Propuesta:** {cotiz['propuesta']}")
            st.markdown(f"**Fecha:** {cotiz['fecha']}")
            st.markdown(f"**Responsable:** {cotiz['responsable']}")

            st.markdown(f"**Total Venta:** ${cotiz['total_venta']:,.2f}")
            st.markdown(f"**Total Costo:** ${cotiz['total_costo']:,.2f}")
            st.markdown(f"**Utilidad:** ${cotiz['utilidad']:,.2f}")
            st.markdown(f"**Margen:** {cotiz['margen']:.2f}%")

            st.markdown("**Productos (Venta):**")
            st.dataframe(productos[productos["tipo_origen"] == "venta"].drop(columns=["cotizacion_id", "tipo_origen"]))

            st.markdown("**Productos (Costo):**")
            st.dataframe(productos[productos["tipo_origen"] == "costo"].drop(columns=["cotizacion_id", "tipo_origen"]))
except:
    st.warning("No se pudo cargar el detalle de cotizaciones.")

# Comparador de cotizaciones
st.subheader("📊 Comparador de propuestas")
try:
    df_hist = ver_historial()

    if not df_hist.empty:
        opciones_multi = df_hist.apply(lambda row: f"{row['id']} - {row['propuesta']} ({row['cliente']})", axis=1)
        seleccion_multi = st.multiselect("Selecciona una o más propuestas para comparar:", opciones_multi)

        if seleccion_multi:
            ids = tuple(int(op.split(" - ")[0]) for op in seleccion_multi)
            conn = conectar_db()
            if len(ids) == 1:
                query = f"SELECT * FROM cotizaciones WHERE id = {ids[0]}"
            else:
                query = f"SELECT * FROM cotizaciones WHERE id IN {ids}"
            comparativo = pd.read_sql_query(query, conn)
            conn.close()

            st.dataframe(comparativo[["id", "cliente", "propuesta", "fecha", "total_venta", "total_costo", "utilidad", "margen"]])
except:
    st.warning("No se pudo mostrar el comparador.")



# Exportar cotización para cliente (Excel)
import io

def exportar_cotizacion_cliente(df_venta, encabezado):
    df_export = df_venta[["Producto", "Cantidad", "Precio Unitario de Lista", "Precio Total con Descuento"]].copy()
    df_export.columns = ["Producto", "Cantidad", "Precio Unitario", "Total"]

    meta = pd.DataFrame({
        "Campo": ["Cliente", "Contacto", "Propuesta", "Fecha", "Responsable"],
        "Valor": [
            encabezado.get("cliente", ""),
            encabezado.get("contacto", ""),
            encabezado.get("propuesta", ""),
            encabezado.get("fecha", ""),
            encabezado.get("responsable", "")
        ]
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        meta.to_excel(writer, index=False, sheet_name="Datos Cliente")
        df_export.to_excel(writer, index=False, sheet_name="Cotización")

        workbook  = writer.book
        worksheet = writer.sheets["Cotización"]
        total_row = len(df_export) + 2
        worksheet.write(f"C{total_row}", "Total General:")
        worksheet.write_formula(f"D{total_row}", f"=SUM(D2:D{len(df_export)+1})")

    output.seek(0)
    return output

# Mostrar botón de exportar si hay datos
if 'df_tabla_descuento' in locals() and not df_tabla_descuento.empty and cliente and propuesta:
    encabezado_cliente = {
        "cliente": cliente,
        "contacto": contacto,
        "propuesta": propuesta,
        "fecha": fecha.strftime('%Y-%m-%d'),
        "responsable": responsable
    }

    excel_file = exportar_cotizacion_cliente(pd.DataFrame(tabla_descuento), encabezado_cliente)
    st.download_button(
        label="📤 Exportar cotización para cliente (Excel)",
        data=excel_file,
        file_name=f"cotizacion_{cliente}_{propuesta}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
