import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
import io

# ========================
# BASE DE DATOS Y CRM
# ========================
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")

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
            margen REAL,
            estatus TEXT DEFAULT 'Borrador'
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
        datos["utilidad"], datos["margen"], datos["estatus"]
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

# Inicializar la base de datos (se crea si no existe)
inicializar_db()

# ========================
# FUNCIONES DE EXPORTACIÓN
# ========================

def exportar_cotizacion_cliente(df_venta, encabezado):
    # Preparar DataFrame para exportar (solo campos visibles para cliente)
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
        df_export.to_excel(writer, index=False, startrow=8, sheet_name="Cotización")

        workbook  = writer.book
        worksheet = writer.sheets["Cotización"]
        worksheet.insert_image("A1", "logo_empresa.png", {"x_scale": 0.3, "y_scale": 0.3})

        bold = workbook.add_format({"bold": True})
        money_border = workbook.add_format({"num_format": "$#,##0.00", "border": 1})
        normal_border = workbook.add_format({"border": 1})
        header_format = workbook.add_format({"bold": True, "bg_color": "#F2F2F2", "border": 1})

        for col_num, _ in enumerate(df_export.columns):
            worksheet.write(7, col_num, df_export.columns[col_num], header_format)
            col_letter = chr(65 + col_num)
            if col_letter in ["C", "D"]:
                worksheet.set_column(f"{col_letter}:{col_letter}", 15, money_border)
            else:
                worksheet.set_column(f"{col_letter}:{col_letter}", 20, normal_border)

        total_row = len(df_export) + 9
        worksheet.write(f"C{total_row}", "Total General:", bold)
        worksheet.write_formula(f"D{total_row}", f"=SUM(D9:D{len(df_export)+8})", money_border)
    output.seek(0)
    return output

def generar_pdf_cotizacion(df_venta, encabezado, logo_path):
    output_path = "cotizacion_cliente.pdf"
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle

    c = canvas.Canvas(output_path, pagesize=LETTER)
    width, height = LETTER

    # Colores institucionales
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

    # Firma de cortesía
    c.setFont("Helvetica", 10)
    c.drawString(inch * 0.5, y_final, "Atentamente,")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inch * 0.5, y_final - 15, encabezado.get("responsable", ""))
    y_final -= 35

    # Condiciones y vigencia
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

# ========================
# INTERFAZ DE USUARIO
# ========================

st.title("Cotizador ThreatDown con CRM")

# Sidebar: Datos de la cotización
st.sidebar.header("Datos de la cotización")
cliente = st.sidebar.text_input("Cliente")
contacto = st.sidebar.text_input("Nombre de contacto")
propuesta = st.sidebar.text_input("Nombre de la propuesta")
fecha = st.sidebar.date_input("Fecha", value=date.today())
responsable = st.sidebar.text_input("Responsable / Vendedor")
estatus = st.sidebar.selectbox("Estatus de la cotización", ["Borrador", "Enviada", "Ganada", "Perdida"])

# Cargar datos de productos desde el archivo Excel en Cloud
@st.cache_data
def cargar_datos():
    df = pd.read_excel("/mnt/data/precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()
terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (en meses):", terminos_disponibles)
df_filtrado_termino = df_precios[df_precios["Term (Month)"] == terminos_disponibles[0]]
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
    st.markdown(f"**Estatus:** {estatus}")

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
    st.markdown("### 📤 Exportación")
    st.markdown("Puedes exportar esta propuesta con formato profesional para tu cliente:")
    if tabla_descuento and cliente and propuesta:
        encabezado_cliente = {
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
    if tabla_descuento and cliente and propuesta:
        encabezado_cliente = {
            "cliente": cliente,
            "contacto": contacto,
            "propuesta": propuesta,
            "fecha": fecha.strftime('%Y-%m-%d'),
            "responsable": responsable
        }
        ruta_pdf = generar_pdf_cotizacion(pd.DataFrame(tabla_descuento), encabezado_cliente, "logo_empresa.png")
        with open(ruta_pdf, "rb") as f:
            st.download_button(
                label="🖨️ Descargar propuesta actual (PDF)",
                data=f,
                file_name=f"cotizacion_{cliente}_{propuesta}.pdf",
                mime="application/pdf"
            )

# Historial de cotizaciones y filtros
st.subheader("📋 Historial de cotizaciones")
filtro_cliente = st.text_input("🔎 Filtrar por cliente:")
filtro_propuesta = st.text_input("🔎 Filtrar por propuesta:")
df_hist = ver_historial()
if filtro_cliente:
    df_hist = df_hist[df_hist["cliente"].str.contains(filtro_cliente, case=False, na=False)]
if filtro_propuesta:
    df_hist = df_hist[df_hist["propuesta"].str.contains(filtro_propuesta, case=False, na=False)]
try:
    df_hist["fecha"] = pd.to_datetime(df_hist["fecha"])
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fecha_inicio = st.date_input("📅 Fecha desde:", value=df_hist["fecha"].min().date())
    with col_f2:
        fecha_fin = st.date_input("📅 Fecha hasta:", value=df_hist["fecha"].max().date())
    df_hist = df_hist[(df_hist["fecha"] >= pd.to_datetime(fecha_inicio)) & (df_hist["fecha"] <= pd.to_datetime(fecha_fin))]
except Exception as e:
    st.info("No se pudieron aplicar filtros de fecha.")
estatus_opciones = ["Todos"] + sorted(df_hist["estatus"].dropna().unique().tolist())
filtro_estatus = st.selectbox("📌 Filtrar por estatus:", estatus_opciones)
if filtro_estatus != "Todos":
    df_hist = df_hist[df_hist["estatus"] == filtro_estatus]
st.dataframe(df_hist[["id", "cliente", "propuesta", "fecha", "total_venta", "total_costo", "utilidad", "margen", "estatus"]])
    
st.subheader("🔍 Ver detalle de cotización guardada")
try:
    opciones = df_hist.apply(lambda row: f"{row['id']} - {row['propuesta']} ({row['cliente']})", axis=1)
    seleccion_detalle = st.selectbox("Selecciona una cotización para ver el detalle:", opciones)
    if seleccion_detalle:
        id_seleccionado = int(seleccion_detalle.split(" - ")[0])
        conn = conectar_db()
        detalle = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {id_seleccionado}", conn)
        productos_detalle = pd.read_sql_query(f"SELECT * FROM detalle_productos WHERE cotizacion_id = {id_seleccionado}", conn)
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
        st.dataframe(productos_detalle[productos_detalle["tipo_origen"] == "venta"].drop(columns=["cotizacion_id", "tipo_origen"]))
        st.markdown("**Productos (Costo):**")
        st.dataframe(productos_detalle[productos_detalle["tipo_origen"] == "costo"].drop(columns=["cotizacion_id", "tipo_origen"]))
        st.markdown("### 📤 Exportación de propuesta guardada")
        st.markdown("Descarga en formato profesional para compartir con tu cliente:")
        encabezado_seleccionado = {
            "cliente": cotiz["cliente"],
            "contacto": cotiz["contacto"],
            "propuesta": cotiz["propuesta"],
            "fecha": cotiz["fecha"],
            "responsable": cotiz["responsable"]
        }
        df_export_guardado = productos_detalle[productos_detalle["tipo_origen"] == "venta"].copy()
        if "precio_unitario" in df_export_guardado.columns:
            df_export_guardado.rename(columns={
                "precio_unitario": "Precio Unitario de Lista",
                "precio_total": "Precio Total con Descuento"
            }, inplace=True)
        ruta_pdf_hist = generar_pdf_cotizacion(pd.DataFrame(df_export_guardado), encabezado_seleccionado, "logo_empresa.png")
        with open(ruta_pdf_hist, "rb") as f:
            st.download_button(
                label="🖨️ Descargar propuesta seleccionada (PDF)",
                data=f,
                file_name=f"cotizacion_{cotiz['cliente']}_{cotiz['propuesta']}.pdf",
                mime="application/pdf"
            )
        st.download_button(
            label="📥 Descargar propuesta seleccionada (Excel)",
            data=exportar_cotizacion_cliente(pd.DataFrame(df_export_guardado), encabezado_seleccionado),
            file_name=f"cotizacion_{cotiz['cliente']}_{cotiz['propuesta']}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
except Exception as e:
    st.warning("No se pudo cargar el detalle de cotizaciones.")

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
    st.warning("No se pudo generar el dashboard.")
