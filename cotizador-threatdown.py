import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
from fpdf import FPDF

# Configuración de la base de datos
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")

# ========================
# Funciones de base de datos
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
            margen REAL,
            vigencia TEXT,
            condiciones_comerciales TEXT
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
        INSERT INTO cotizaciones (
            cliente, contacto, propuesta, fecha, responsable,
            total_venta, total_costo, utilidad, margen, vigencia, condiciones_comerciales
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["total_venta"], datos["total_costo"],
        datos["utilidad"], datos["margen"], datos["vigencia"], datos["condiciones_comerciales"]
    ))
    cotizacion_id = cursor.lastrowid

    for p in productos_venta:
        cursor.execute("""
            INSERT INTO detalle_productos (
                cotizacion_id, producto, cantidad, precio_unitario,
                precio_total, descuento_aplicado, tipo_origen
            ) VALUES (?, ?, ?, ?, ?, ?, 'venta')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Unitario Lista"],
            p["Subtotal"], p["Descuento %"]
        ))

    for p in productos_costo:
        cursor.execute("""
            INSERT INTO detalle_productos (
                cotizacion_id, producto, cantidad, precio_unitario,
                precio_total, descuento_aplicado, tipo_origen
            ) VALUES (?, ?, ?, ?, ?, ?, 'costo')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Base"],
            p["Subtotal"], p["Item Disc. %"] + p["Channel + Deal Disc. %"]
        ))

    conn.commit()
    conn.close()
    return cotizacion_id

def ver_historial():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM cotizaciones ORDER BY fecha DESC", conn)
    conn.close()
    return df

# Inicializar base de datos
inicializar_db()

# ========================
# Configuración inicial
# ========================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()

# Configurar estado de sesión
if 'cotizacion_activa' not in st.session_state:
    st.session_state.cotizacion_activa = {
        'productos_costo': [],
        'productos_venta': [],
        'datos_generales': {}
    }

# ========================
# Interfaz de usuario
# ========================
st.title("Cotizador ThreatDown con CRM")

# Sidebar con datos generales
st.sidebar.header("Datos de la cotización")
cliente = st.sidebar.text_input("Cliente")
contacto = st.sidebar.text_input("Nombre de contacto")
propuesta = st.sidebar.text_input("Nombre de la propuesta")
fecha = st.sidebar.date_input("Fecha", value=date.today())
responsable = st.sidebar.text_input("Responsable / Vendedor")

# Sección para agregar productos
st.header("Agregar productos a la cotización")

# Selectores de producto
terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
termino_seleccionado = st.selectbox(
    "Plazo del servicio (meses):",
    terminos_disponibles,
    key='termino_actual'
)

df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado]
productos_disponibles = df_filtrado_termino["Product Title"].unique()
producto_seleccionado = st.selectbox(
    "Seleccionar producto:",
    productos_disponibles,
    key='producto_actual'
)

# Campos de descuentos
col1, col2, col3, col4 = st.columns(4)
with col1:
    cantidad = st.number_input("Cantidad:", min_value=1, value=1, step=1)
with col2:
    item_disc = st.number_input("Item Disc. %:", 0.0, 100.0, 0.0, step=0.5)
with col3:
    channel_disc = st.number_input("Channel Disc. %:", 0.0, 100.0, 0.0, step=0.5)
with col4:
    deal_reg_disc = st.number_input("Deal Reg. Disc. %:", 0.0, 100.0, 0.0, step=0.5)

direct_discount = st.number_input(
    "Descuento directo sobre lista (%):",
    0.0, 100.0, 0.0, step=0.5,
    key='directo_actual'
)

# Botón para agregar producto
if st.button("➕ Agregar producto a la cotización"):
    df_producto = df_filtrado_termino[
        (df_filtrado_termino["Product Title"] == producto_seleccionado)
    ].iloc[0]
    
    precio_base = df_producto["MSRP USD"]
    
    # Cálculos para costo
    precio_costo = precio_base * (1 - item_disc/100) * (1 - (channel_disc + deal_reg_disc)/100)
    subtotal_costo = precio_costo * cantidad
    
    # Cálculos para venta
    precio_venta = precio_base * (1 - direct_discount/100)
    subtotal_venta = precio_venta * cantidad
    
    # Guardar en sesión
    nuevo_producto_costo = {
        "Producto": producto_seleccionado,
        "Cantidad": cantidad,
        "Precio Base": precio_base,
        "Item Disc. %": item_disc,
        "Channel + Deal Disc. %": channel_disc + deal_reg_disc,
        "Subtotal": subtotal_costo
    }
    
    nuevo_producto_venta = {
        "Producto": producto_seleccionado,
        "Cantidad": cantidad,
        "Precio Unitario Lista": precio_base,
        "Descuento %": direct_discount,
        "Subtotal": subtotal_venta
    }
    
    st.session_state.cotizacion_activa['productos_costo'].append(nuevo_producto_costo)
    st.session_state.cotizacion_activa['productos_venta'].append(nuevo_producto_venta)
    st.success(f"Producto {producto_seleccionado} agregado!")

# Mostrar productos agregados
st.subheader("Productos en la cotización actual")

if st.session_state.cotizacion_activa['productos_costo']:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Costos**")
        df_costo = pd.DataFrame(st.session_state.cotizacion_activa['productos_costo'])
        st.dataframe(df_costo)
        
    with col2:
        st.markdown("**Ventas**")
        df_venta = pd.DataFrame(st.session_state.cotizacion_activa['productos_venta'])
        st.dataframe(df_venta)
        
    # Calcular totales
    total_costo = df_costo['Subtotal'].sum()
    total_venta = df_venta['Subtotal'].sum()
    utilidad = total_venta - total_costo
    margen = (utilidad / total_venta) * 100 if total_venta > 0 else 0
    
    st.subheader("Totales")
    st.markdown(f"""
    - **Total Costo:** ${total_costo:,.2f}
    - **Total Venta:** ${total_venta:,.2f}
    - **Utilidad:** ${utilidad:,.2f}
    - **Margen:** {margen:.2f}%
    """)
else:
    st.info("Aún no hay productos en la cotización")

# Sección para guardar la cotización
st.header("Finalizar cotización")
vigencia = st.text_input("Vigencia de la propuesta:", "30 días")
condiciones = st.text_area(
    "Condiciones comerciales:",
    value="Precios en USD. Pago contra entrega. No incluye impuestos. Licenciamiento anual.",
    height=150
)

if st.button("💾 Guardar cotización completa"):
    if not cliente or not propuesta:
        st.error("Debe completar los campos obligatorios: Cliente y Propuesta")
    else:
        datos = {
            "cliente": cliente,
            "contacto": contacto,
            "propuesta": propuesta,
            "fecha": fecha.strftime('%Y-%m-%d'),
            "responsable": responsable,
            "total_venta": total_venta,
            "total_costo": total_costo,
            "utilidad": utilidad,
            "margen": margen,
            "vigencia": vigencia,
            "condiciones_comerciales": condiciones
        }
        
        try:
            cotizacion_id = guardar_cotizacion(
                datos,
                st.session_state.cotizacion_activa['productos_venta'],
                st.session_state.cotizacion_activa['productos_costo']
            )
            
            # Limpiar cotización actual
            st.session_state.cotizacion_activa = {
                'productos_costo': [],
                'productos_venta': [],
                'datos_generales': {}
            }
            
            st.success(f"Cotización #{cotizacion_id} guardada exitosamente!")
        except Exception as e:
            st.error(f"Error al guardar: {str(e)}")

# Historial de cotizaciones
st.header("📋 Historial de cotizaciones")
try:
    df_hist = ver_historial()
    st.dataframe(df_hist)
except:
    st.warning("No hay cotizaciones guardadas aún.")

# Generador de PDF
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
            self.cell(60, 8, str(p["Producto"]), 1)
            self.cell(20, 8, str(p["Cantidad"]), 1, align="C")
            self.cell(30, 8, f"${p['Precio Unitario Lista']:,.2f}", 1, align="R")
            self.cell(30, 8, f"{p['Descuento %']}%", 1, align="R")
            self.cell(40, 8, f"${p['Subtotal']:,.2f}", 1, ln=True, align="R")
        self.ln(5)

    def totales(self, total_venta):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Total de la propuesta: ${total_venta:,.2f}", ln=True, align="R")
        self.ln(10)

    def condiciones(self, vigencia, condiciones):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 6, f"""
            Vigencia: {vigencia}
            Condiciones comerciales:
            {condiciones}
        """)
        self.ln(10)

    def firma(self):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, "Atentamente,", ln=True)
        self.cell(0, 8, "Salvador Pérez | Director de Tecnología", ln=True)
        self.cell(0, 8, "SYNAPPSSYS", ln=True)

# Sección para generar PDF
st.header("🔍 Ver detalle de cotización")
conn = conectar_db()
df_cotizaciones = pd.read_sql_query("SELECT id, propuesta, cliente, fecha FROM cotizaciones ORDER BY fecha DESC", conn)

if not df_cotizaciones.empty:
    df_cotizaciones["Resumen"] = df_cotizaciones["fecha"] + " - " + df_cotizaciones["cliente"] + " - " + df_cotizaciones["propuesta"]
    seleccion_resumen = st.selectbox("Selecciona una cotización para ver el detalle:", df_cotizaciones["Resumen"])
    
    if seleccion_resumen:
        cotizacion_id = int(df_cotizaciones[df_cotizaciones["Resumen"] == seleccion_resumen]["id"].values[0])
        
        # Obtener datos de la cotización
        datos = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {cotizacion_id}", conn).iloc[0]
        productos_venta = pd.read_sql_query(f"""
            SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado 
            FROM detalle_productos 
            WHERE cotizacion_id = {cotizacion_id} AND tipo_origen = 'venta'
        """, conn)
        
        # Generar PDF
        if st.button("📄 Generar PDF para cliente"):
            pdf = CotizacionPDFConLogo()
            pdf.add_page()
            
            datos_cliente = {
                "cliente": datos["cliente"],
                "contacto": datos["contacto"],
                "propuesta": datos["propuesta"],
                "fecha": datos["fecha"],
                "responsable": datos["responsable"]
            }
            
            productos = productos_venta.to_dict("records")
            
            pdf.encabezado_cliente(datos_cliente)
            pdf.tabla_productos(productos)
            pdf.totales(datos["total_venta"])
            pdf.condiciones(datos["vigencia"], datos["condiciones_comerciales"])
            pdf.firma()
            
            pdf_output_path = f"cotizacion_{cotizacion_id}.pdf"
            pdf.output(pdf_output_path)
            
            with open(pdf_output_path, "rb") as file:
                st.download_button(
                    label="📥 Descargar PDF",
                    data=file,
                    file_name=pdf_output_path,
                    mime="application/pdf"
                )
            
            os.remove(pdf_output_path)

conn.close()
