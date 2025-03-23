
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import os

def generar_pdf_cotizacion(df_venta, encabezado, logo_path):
    output_path = "cotizacion_cliente.pdf"
    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    color_fondo = colors.HexColor("#003366")
    color_texto_header = colors.white

    if logo_path and os.path.exists(logo_path):
        c.drawImage(logo_path, inch * 0.5, height - inch * 1.2, width=100, preserveAspectRatio=True, mask='auto')

    y = height - inch * 1.4
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(color_fondo)
    c.drawString(inch * 3, y, "COTIZACIÓN COMERCIAL")
    c.setFillColor(colors.black)
    y -= 30

    c.setFont("Helvetica", 10)
    for campo in ["cliente", "contacto", "propuesta", "fecha", "responsable"]:
        valor = encabezado.get(campo, "")
        c.drawString(inch * 0.5, y, f"{campo.capitalize()}: {valor}")
        y -= 15

    y -= 5
    c.setFont("Helvetica-Bold", 11)
    c.drawString(inch * 0.5, y, "Detalle de productos:")
    y -= 20

    data = [["Producto", "Cantidad", "Precio Unitario", "Total"]]
    total = 0
    for _, row in df_venta.iterrows():
        data.append([
            row["Producto"],
            str(row["Cantidad"]),
            f"${row['Precio Unitario de Lista']:,.2f}",
            f"${row['Precio Total con Descuento']:,.2f}"
        ])
        total += row["Precio Total con Descuento"]

    data.append(["", "", "Total:", f"${total:,.2f}"])

    table = Table(data, colWidths=[240, 60, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), color_fondo),
        ('TEXTCOLOR', (0, 0), (-1, 0), color_texto_header),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    table.wrapOn(c, width, height)
    table_height = len(data) * 18
    table.drawOn(c, inch * 0.5, y - table_height)

    y_final = y - table_height - 30

    c.setFont("Helvetica", 10)
    c.drawString(inch * 0.5, y_final, "Atentamente,")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch * 0.5, y_final - 15, encabezado.get("responsable", ""))
    y_final -= 35

    c.setFont("Helvetica-Oblique", 8)
    condiciones = [
        "Cotización válida por 15 días.",
        "Precios en USD más IVA.",
        "Sujeto a disponibilidad de producto.",
        "Para dudas o aclaraciones, contáctenos a contacto@synappssys.com"
    ]
    for cond in condiciones:
        c.drawString(inch * 0.5, y_final, cond)
        y_final -= 12

    c.save()
    return output_path



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
        INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen, estatus)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

estatus = st.sidebar.selectbox("Estatus de la cotización", ["Borrador", "Enviada", "Ganada", "Perdida"])

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
        st.markdown("### 📤 Exportación")
        st.markdown("Puedes exportar esta propuesta con formato profesional para tu cliente:")
    
    if tabla_descuento and cliente and propuesta:    encabezado_cliente = {
    "cliente": cliente,
    "contacto": contacto,
    "propuesta": propuesta,
    "fecha": fecha.strftime('%Y-%m-%d'),
    "responsable": responsable
    }
        df_exportable = pd.DataFrame(tabla_descuento)
    excel_file = exportar_cotizacion_cliente(df_exportable, encabezado_cliente)
        st.download_button(
        label="📥 Descargar propuesta actual (Excel)",
    data=excel_file,
    file_name=f"cotizacion_{cliente}_{propuesta}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
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
    ,
    "estatus": estatus}
    guardar_cotizacion(datos, df_tabla_descuento.to_dict("records"), df_cotizacion.to_dict("records"))
    st.success("✅ Cotización guardada en CRM")
    st.subheader("📋 Historial de cotizaciones")
try:
    df_hist = ver_historial()

# === Filtros de búsqueda en historial ===
filtro_cliente = st.text_input("🔎 Filtrar por cliente:")
filtro_propuesta = st.text_input("🔎 Filtrar por propuesta:")

if filtro_cliente:
    df_hist = df_hist[df_hist["cliente"].str.contains(filtro_cliente, case=False, na=False)]

if filtro_propuesta:
    df_hist = df_hist[df_hist["propuesta"].str.contains(filtro_propuesta, case=False, na=False)]

# === Nuevos filtros ===
col_f1, col_f2 = st.columns(2)
with col_f1:
    fecha_inicio = st.date_input("📅 Fecha desde:", value=pd.to_datetime(df_hist["fecha"]).min().date())
with col_f2:
    fecha_fin = st.date_input("📅 Fecha hasta:", value=pd.to_datetime(df_hist["fecha"]).max().date())

df_hist["fecha"] = pd.to_datetime(df_hist["fecha"])
df_hist = df_hist[(df_hist["fecha"] >= pd.to_datetime(fecha_inicio)) & (df_hist["fecha"] <= pd.to_datetime(fecha_fin))]

# Filtro por estatus
estatus_opciones = ["Todos"] + sorted(df_hist["estatus"].dropna().unique().tolist())
filtro_estatus = st.selectbox("📌 Filtrar por estatus:", estatus_opciones)
if filtro_estatus != "Todos":
    df_hist = df_hist[df_hist["estatus"] == filtro_estatus]
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
            # Botón para exportar cotización guardada
            encabezado_seleccionado = {
                "cliente": cotiz["cliente"],
                "contacto": cotiz["contacto"],
                "propuesta": cotiz["propuesta"],
                "fecha": cotiz["fecha"],
                "responsable": cotiz["responsable"]
            }

            df_export_guardado = productos[productos["tipo_origen"] == "venta"].copy()
            df_export_guardado.rename(columns={{
                "precio_unitario": "Precio Unitario de Lista",
                "precio_total": "Precio Total con Descuento"
            }}, inplace=True)

            archivo_exportado = exportar_cotizacion_cliente(df_export_guardado, encabezado_seleccionado)

            
st.markdown("### 📤 Exportación de propuesta seleccionada")
st.markdown("Descarga en formato profesional para compartir con tu cliente:")

st.download_button(
    label="📥 Descargar propuesta seleccionada (Excel)",

st.markdown("🖨️ También puedes exportar esta propuesta en formato PDF:")

# Preparar datos para PDF
encabezado_pdf = {
    "cliente": cotiz["cliente"],
    "contacto": cotiz["contacto"],
    "propuesta": cotiz["propuesta"],
    "fecha": cotiz["fecha"],
    "responsable": cotiz["responsable"]
}
df_export_hist = productos[productos["tipo_origen"] == "venta"].copy()
df_export_hist.rename(columns={
    "precio_unitario": "Precio Unitario de Lista",
    "precio_total": "Precio Total con Descuento"
}, inplace=True)

ruta_pdf_hist = generar_pdf_cotizacion(df_export_hist, encabezado_pdf, "logo_empresa.png")
with open(ruta_pdf_hist, "rb") as f:
    st.download_button(
        label="🖨️ Descargar propuesta seleccionada (PDF)",
        data=f,
        file_name=f"cotizacion_{cotiz['cliente']}_{cotiz['propuesta']}.pdf",
        mime="application/pdf"
    )


                data=archivo_exportado,
                file_name=f"cotizacion_{cotiz['cliente']}_{cotiz['propuesta']}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

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



# Mostrar botón de exportar si hay datos
if tabla_descuento and cliente and propuesta:    encabezado_cliente = {
    "cliente": cliente,
    "contacto": contacto,
    "propuesta": propuesta,
    "fecha": fecha.strftime('%Y-%m-%d'),
    "responsable": responsable
    }
        df_exportable = pd.DataFrame(tabla_descuento)
    excel_file = exportar_cotizacion_cliente(df_exportable, encabezado_cliente)
    st.download_button(
    label="📤 Exportar cotización para cliente (Excel)",
    data=excel_file,
    file_name=f"cotizacion_{cliente}_{propuesta}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
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
        meta.to_excel(writer, index=False, sheet_name="Cotización")
        df_export.to_excel(writer, index=False, startrow=8, sheet_name="Cotización")

        workbook  = writer.book
        worksheet = writer.sheets["Cotización"]

        worksheet.insert_image("A1", "logo_empresa.png", { "x_scale": 0.3, "y_scale": 0.3 })

        bold = workbook.add_format({"bold": True})
        money = workbook.add_format({"num_format": "$#,##0.00"})
        header_format = workbook.add_format({"bold": True, "bg_color": "#F2F2F2", "border": 1})
        normal_border = workbook.add_format({"border": 1})
        money_border = workbook.add_format({"num_format": "$#,##0.00", "border": 1})

        for col_num, _ in enumerate(df_export.columns):
            worksheet.write(7, col_num, df_export.columns[col_num], header_format)
            col_letter = chr(65 + col_num)
            if col_letter in ["C", "D"]:
                worksheet.set_column(f"{col_letter}:{col_letter}", 15, money_border)
            else:
                worksheet.set_column(f"{col_letter}:{col_letter}", 20, normal_border)

        total_row = 8 + len(df_export) + 1
        worksheet.write(f"C{total_row}", "Total General:", bold)
        worksheet.write_formula(f"D{total_row}", f"=SUM(D9:D{8+len(df_export)})", money)

    output.seek(0)
    return output



# ========================
# DASHBOARD DE MÉTRICAS
# ========================
st.markdown("---")
st.header("📊 Dashboard de Cotizaciones")

try:
    df_dash = ver_historial()
    df_dash["fecha"] = pd.to_datetime(df_dash["fecha"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cotizaciones totales", len(df_dash))
    col2.metric("Total cotizado", f"${df_dash['total_venta'].sum():,.2f}")
    col3.metric("Utilidad total", f"${df_dash['utilidad'].sum():,.2f}")
    margen_prom = df_dash["margen"].mean()
    col4.metric("Margen promedio", f"{margen_prom:.2f}%")

    st.subheader("🎯 Clientes más frecuentes")
    clientes_top = df_dash["cliente"].value_counts().reset_index()
    clientes_top.columns = ["Cliente", "Propuestas"]
    st.dataframe(clientes_top)

    st.subheader("📌 Cotizaciones por estatus")
    estatus_count = df_dash["estatus"].value_counts().reset_index()
    estatus_count.columns = ["Estatus", "Cantidad"]
    st.dataframe(estatus_count)
except Exception as e:
    st.warning("No se pudo generar el dashboard."


# Exportar propuesta actual como PDF
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle




# Mostrar botón solo si hay propuesta actual válida
if tabla_descuento and cliente and propuesta:    df_pdf = pd.DataFrame(tabla_descuento)
    encabezado_pdf = {
    "cliente": cliente,
    "contacto": contacto,
    "propuesta": propuesta,
    "fecha": fecha.strftime('%Y-%m-%d'),
    "responsable": responsable
    }
    ruta_pdf = generar_pdf_cotizacion(df_pdf, encabezado_pdf, "logo_empresa.png")
    with open(ruta_pdf, "rb") as f:
    st.download_button(
    label="🖨️ Descargar propuesta actual (PDF)",
    data=f,
    file_name=f"cotizacion_{cliente}_{propuesta}.pdf",
    mime="application/pdf"
    )
    )
