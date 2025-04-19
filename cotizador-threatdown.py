import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
import io
import bcrypt

# ========================
# Configuración inicial
# ========================

st.set_page_config(page_title="Cotizador ThreatDown", layout="wide")

# Inicializar variables de sesión
for key in ["df_tabla_descuento", "df_cotizacion", "cliente", "contacto", "propuesta", "fecha", "responsable"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "fecha" else date.today()

# Crear ruta segura para base de datos en entorno escribible
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")

# ========================
# Funciones de autenticación
# ========================

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verificar_password(password_ingresada, password_hash_guardada):
    return bcrypt.checkpw(password_ingresada.encode(), password_hash_guardada.encode())

def autenticar_usuario(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM usuarios WHERE username = ?", (username,))
    resultado = cursor.fetchone()
    conn.close()
    if resultado:
        return verificar_password(password, resultado[0])
    return False

# ========================
# Funciones de base de datos
# ========================

def inicializar_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            rol TEXT DEFAULT 'usuario'
        )
    """)
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

# ========================
# Login de usuario
# ========================

inicializar_db()

if "usuario_autenticado" not in st.session_state:
    st.session_state.usuario_autenticado = False

if not st.session_state.usuario_autenticado:
    st.title("Inicio de sesión")
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    if st.button("Iniciar sesión"):
        if autenticar_usuario(username, password):
            st.session_state.usuario_autenticado = True
            st.experimental_rerun()
        else:
            st.error("Usuario o contraseña incorrectos")
    st.stop()


# ========================
# Configuración inicial
# ========================

st.set_page_config(page_title="Cotizador ThreatDown", layout="wide")

# Inicializar variables de sesión
for key in ["df_tabla_descuento", "df_cotizacion", "cliente", "contacto", "propuesta", "fecha", "responsable"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "fecha" else date.today()

# Crear ruta segura para base de datos en entorno escribible
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

# ========================
# Cargar archivo de datos
# ========================

@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()

# ========================
# Interfaz principal
# ========================

st.title("Cotizador ThreatDown con CRM")
inicializar_db()

# ========================
# Entradas del usuario
# ========================
st.sidebar.header("Datos de la cotización")
st.session_state.cliente = st.sidebar.text_input("Cliente", value=st.session_state.cliente or "")
st.session_state.contacto = st.sidebar.text_input("Nombre de contacto", value=st.session_state.contacto or "")
st.session_state.propuesta = st.sidebar.text_input("Nombre de la propuesta", value=st.session_state.propuesta or "")
st.session_state.fecha = st.sidebar.date_input("Fecha", value=st.session_state.fecha)
st.session_state.responsable = st.sidebar.text_input("Responsable / Vendedor", value=st.session_state.responsable or "")

# ========================
# Selección de productos
# ========================
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

# ========================
# Mostrar datos del cliente
# ========================
if st.session_state.cliente or st.session_state.propuesta or st.session_state.responsable:
    st.subheader("Datos de la cotización")
    st.markdown(f"**Cliente:** {st.session_state.cliente}")
    st.markdown(f"**Contacto:** {st.session_state.contacto}")
    st.markdown(f"**Propuesta:** {st.session_state.propuesta}")
    st.markdown(f"**Fecha:** {st.session_state.fecha.strftime('%Y-%m-%d')}")
    st.markdown(f"**Responsable:** {st.session_state.responsable}")

# ========================
# Cotización (costos y venta)
# ========================

costo_total = 0
if cotizacion:
    st.session_state.df_cotizacion = pd.DataFrame(cotizacion)
    st.subheader("Resumen de Cotización (costos)")
    st.dataframe(st.session_state.df_cotizacion)
    costo_total = st.session_state.df_cotizacion["Subtotal"].sum()
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

        descuento_directo = st.number_input(
            f"Descuento directo (%) sobre lista para '{prod}':",
            0.0, 100.0, 0.0, key=f"direct_discount_{prod}"
        )
        precio_con_descuento = precio_total_lista * (1 - descuento_directo / 100)

        tabla_descuento.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Unitario de Lista": round(precio_unitario, 2),
            "Precio Total de Lista": round(precio_total_lista, 2),
            "Descuento %": descuento_directo,
            "Precio Total con Descuento": round(precio_con_descuento, 2)
        })

    st.session_state.df_tabla_descuento = pd.DataFrame(tabla_descuento)
    st.dataframe(st.session_state.df_tabla_descuento)
    precio_venta_total = st.session_state.df_tabla_descuento["Precio Total con Descuento"].sum()
    st.success(f"Precio total de venta: ${precio_venta_total:,.2f}")

# ========================
# Guardar cotización
# ========================
if precio_venta_total > 0 and costo_total > 0:
    utilidad = precio_venta_total - costo_total
    margen = (utilidad / precio_venta_total) * 100

    st.subheader("Utilidad de la operación")
    col1, col2 = st.columns(2)
    col1.metric("Utilidad total", f"${utilidad:,.2f}")
    col2.metric("Margen (%)", f"{margen:.2f}%")

    if st.button("💾 Guardar cotización"):
        datos = {
            "cliente": st.session_state.cliente,
            "contacto": st.session_state.contacto,
            "propuesta": st.session_state.propuesta,
            "fecha": st.session_state.fecha.strftime('%Y-%m-%d'),
            "responsable": st.session_state.responsable,
            "total_venta": precio_venta_total,
            "total_costo": costo_total,
            "utilidad": utilidad,
            "margen": margen
        }

        guardar_cotizacion(datos,
                           st.session_state.df_tabla_descuento.to_dict("records"),
                           st.session_state.df_cotizacion.to_dict("records"))
        st.success("✅ Cotización guardada en CRM")

# ========================
# Exportar a Excel
# ========================

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
        worksheet = writer.sheets["Cotización"]
        worksheet.write(f"C{len(df_export)+2}", "Total General:")
        worksheet.write_formula(f"D{len(df_export)+2}", f"=SUM(D2:D{len(df_export)+1})")

    output.seek(0)
    return output

if (
    st.session_state.df_tabla_descuento is not None and
    not st.session_state.df_tabla_descuento.empty and
    st.session_state.cliente and st.session_state.propuesta
):
    encabezado_cliente = {
        "cliente": st.session_state.cliente,
        "contacto": st.session_state.contacto,
        "propuesta": st.session_state.propuesta,
        "fecha": st.session_state.fecha.strftime('%Y-%m-%d'),
        "responsable": st.session_state.responsable
    }

    excel_file = exportar_cotizacion_cliente(st.session_state.df_tabla_descuento, encabezado_cliente)
    st.download_button(
        label="📤 Exportar cotización para cliente (Excel)",
        data=excel_file,
        file_name=f"cotizacion_{st.session_state.cliente}_{st.session_state.propuesta}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
