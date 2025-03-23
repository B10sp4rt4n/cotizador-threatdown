
import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date

import shutil
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
            cargo TEXT,
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
        INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable, cargo, total_venta, total_costo, utilidad, margen)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["cargo"], datos["total_venta"], datos["total_costo"],
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

# Eliminar base de datos anterior para desarrollo (opcional)
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

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
responsable = st.sidebar.text_input("Responsable / Quien entrega la propuesta")
cargo_responsable = st.sidebar.text_input("Cargo del responsable")
condiciones_comerciales = st.sidebar.text_area("Condiciones comerciales", value=
    "Vigencia de la propuesta: 30 días naturales.\n"
    "Precios en USD, no incluyen IVA.\n"
    "Condiciones de pago: 50% anticipo, 50% contra entrega."
)

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
            "cargo": cargo_responsable,
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



# =============================
# Ver detalle de cotización seleccionada
# =============================
st.subheader("🔍 Ver detalle de cotización")

conn = conectar_db()
df_cotizaciones = pd.read_sql_query("SELECT id, propuesta, cliente, fecha FROM cotizaciones ORDER BY fecha DESC", conn)

if df_cotizaciones.empty:
    st.info("No hay cotizaciones guardadas para mostrar el detalle.")
else:
    df_cotizaciones["Resumen"] = df_cotizaciones["fecha"] + " - " + df_cotizaciones["cliente"] + " - " + df_cotizaciones["propuesta"]
    seleccion_resumen = st.selectbox("Selecciona una cotización para ver el detalle:", df_cotizaciones["Resumen"])
    
    if seleccion_resumen:
        cotizacion_id = int(df_cotizaciones[df_cotizaciones["Resumen"] == seleccion_resumen]["id"].values[0])
        
        # Datos generales
        datos = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {cotizacion_id}", conn).iloc[0]
        st.markdown(f"**Cliente:** {datos['cliente']}")
        st.markdown(f"**Contacto:** {datos['contacto']}")
        st.markdown(f"**Propuesta:** {datos['propuesta']}")
        st.markdown(f"**Fecha:** {datos['fecha']}")
        st.markdown(f"**Responsable:** {datos['responsable']}")
        st.markdown(f"**Cargo:** {datos['cargo']}")
        st.markdown(f"**Total Venta:** ${datos['total_venta']:,.2f}")
        st.markdown(f"**Total Costo:** ${datos['total_costo']:,.2f}")
        st.markdown(f"**Utilidad:** ${datos['utilidad']:,.2f}")
        st.markdown(f"**Margen:** {datos['margen']:.2f}%")

        # Productos de venta
        st.markdown("### Productos cotizados (venta)")
        df_venta = pd.read_sql_query(f'''
            SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
            FROM detalle_productos
            WHERE cotizacion_id = {cotizacion_id} AND tipo_origen = 'venta'
        ''', conn)
        st.dataframe(df_venta)

        # Productos de costo
        st.markdown("### Productos base (costos)")
        df_costo = pd.read_sql_query(f'''
            SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
            FROM detalle_productos
            WHERE cotizacion_id = {cotizacion_id} AND tipo_origen = 'costo'
        ''', conn)
        st.dataframe(df_costo)

conn.close()


from fpdf import FPDF

class CotizacionPDFConLogo(FPDF):
    def header(self):
        self.image("LOGO Syn Apps Sys_edited (2).png", x=10, y=8, w=50)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(70, 12)
        self.cell(0, 10, "Cotización de Servicios", ln=True, align="L")
        self.ln(20)

    def encabezado_cliente(self, datos):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, f"Cliente: {datos['cliente']}", ln=True)
        self.cell(0, 8, f"Contacto: {datos['contacto']}", ln=True)
        self.cell(0, 8, f"Propuesta: {datos['propuesta']}", ln=True)
        self.cell(0, 8, f"Fecha: {datos['fecha']}", ln=True)
        self.cell(0, 8, f"Responsable: {datos['responsable']}", ln=True)
        self.ln(5)

    def tabla_productos(self, productos):
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 8, "Producto", 1)
        self.cell(20, 8, "Cantidad", 1, align="C")
        self.cell(30, 8, "P. Unitario", 1, align="R")
        self.cell(30, 8, "Descuento %", 1, align="R")
        self.cell(40, 8, "Total", 1, ln=True, align="R")

        self.set_font("Helvetica", "", 10)
        for p in productos:
            self.cell(60, 8, str(p["producto"]), 1)
            self.cell(20, 8, str(p["cantidad"]), 1, align="C")
            self.cell(30, 8, f"${p['precio_unitario']:,.2f}", 1, align="R")
            self.cell(30, 8, f"{p['descuento_aplicado']}%", 1, align="R")
            self.cell(40, 8, f"${p['precio_total']:,.2f}", 1, ln=True, align="R")
        self.ln(5)

    def totales(self, total_venta):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Total de la propuesta: ${total_venta:,.2f}", ln=True, align="R")
        self.ln(10)

    def condiciones(self):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 6,
            "Vigencia de la propuesta: 30 días naturales.\n"
            "Precios en USD, no incluyen IVA.\n"
            "Condiciones de pago: 50% anticipo, 50% contra entrega.\n"
        )
        self.ln(10)

    def firma(self):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, "Atentamente,", ln=True)
        self.cell(0, 8, f"{self.responsable}", ln=True)
        self.cell(0, 8, f"{self.cargo}", ln=True)
        self.cell(0, 8, "SYNAPPSSYS", ln=True)

# Botón para generar PDF desde vista de detalle
if 'cotizacion_id' in locals():
    if st.button("📄 Generar PDF para cliente"):
        pdf = CotizacionPDFConLogo()
        pdf.responsable = datos["responsable"]
        pdf.cargo = datos["cargo"]
        pdf.add_page()

        datos_dict = {
            "cliente": datos["cliente"],
            "contacto": datos["contacto"],
            "propuesta": datos["propuesta"],
            "fecha": datos["fecha"],
            "responsable": datos["responsable"]
        }
        productos = df_venta.to_dict("records")
        total_venta = datos["total_venta"]

        pdf.encabezado_cliente(datos_dict)
        pdf.tabla_productos(productos)
        pdf.totales(total_venta)
        pdf.condiciones()
        pdf.firma()

        pdf_output_path = f"cotizacion_cliente_{cotizacion_id}.pdf"
        pdf.output(pdf_output_path)
        with open(pdf_output_path, "rb") as file:
            st.download_button(
                label="📥 Descargar PDF de cotización",
                data=file,
                file_name=pdf_output_path,
                mime="application/pdf"
            )
