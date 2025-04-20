# Cotizador ThreatDown V17 con autenticación y roles de usuario

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
from datetime import date
from fpdf import FPDF

DB_PATH = "crm_cotizaciones.sqlite"

# =================== Funciones de autenticación ===================
def conectar_db():
    return sqlite3.connect(DB_PATH)

def hash_password(password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    print(f"[LOG] Contraseña hasheada: {hashed}")
    return hashed

def autenticar_usuario(correo, contrasena):
    print(f"[LOG] Intentando autenticar usuario: {correo}")
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, nombre, tipo_usuario, admin_id FROM usuarios
        WHERE correo = ? AND contraseña = ?
    """, (correo, hash_password(contrasena)))
    usuario = cursor.fetchone()
    conn.close()
    print(f"[LOG] Resultado de autenticación: {usuario}")
    return usuario

def crear_usuario(nombre, correo, contrasena, tipo_usuario, admin_id):
    print(f"[LOG] Creando usuario: {nombre}, tipo: {tipo_usuario}, admin_id: {admin_id}")
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usuarios (nombre, correo, contraseña, tipo_usuario, admin_id)
        VALUES (?, ?, ?, ?, ?)
    """, (nombre, correo, hash_password(contrasena), tipo_usuario, admin_id))
    conn.commit()
    conn.close()
    print("[LOG] Usuario creado exitosamente")

# =================== Inicializar base de datos ===================
def inicializar_db():
# Agregar este bloque justo después de `inicializar_db()` como una llamada en el flujo principal
lineas = contenido.splitlines()
nuevas_lineas = []
insertado = False

for i, linea in enumerate(lineas):
    nuevas_lineas.append(linea)
    if not insertado and "inicializar_db()" in linea:
        nuevas_lineas.append(bloque_refuerzo_limpio)
        insertado = True

# Guardar archivo corregido sin errores de indentación
with open(archivo_reparado2, "w", encoding="utf-8") as f:
    f.write("\n".join(nuevas_lineas))

# Comprimir como ZIP
zip_reparado2 = Path("/mnt/data/cotizador-threatdown_reparado2.zip")
with zipfile.ZipFile(zip_reparado2, "w") as zipf:
    zipf.write(archivo_reparado2, arcname="cotizador-threatdown_reparado2.py")

zip_reparado2.name
# Reforzar que la tabla 'clientes' exista antes de continuar
try:
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            apellido_paterno TEXT,
            apellido_materno TEXT,
            empresa TEXT,
            correo TEXT,
            telefono TEXT,
            rfc TEXT,
            calle TEXT,
            numero_exterior TEXT,
            numero_interior TEXT,
            codigo_postal TEXT,
            municipio TEXT,
            ciudad TEXT,
            estado TEXT,
            notas TEXT
        )
    """)
    conn.commit()
    conn.close()
except Exception as e:
    st.error("❌ Error al garantizar existencia de la tabla 'clientes'.")
    st.stop()

    print("[LOG] Inicializando base de datos si no existe")
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            correo TEXT UNIQUE,
            contraseña TEXT,
            tipo_usuario TEXT,
            admin_id INTEGER,
            FOREIGN KEY (admin_id) REFERENCES usuarios(id)
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
            margen REAL,
            vigencia TEXT,
            condiciones_comerciales TEXT,
            usuario_id INTEGER
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
    print("[LOG] Base de datos lista")

# Ejecutar inicialización antes de cualquier uso de tablas
inicializar_db()

# =================== Verificar sesión o mostrar login ===================
def actualizar_contrasena(correo, nueva_contrasena):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET contraseña = ? WHERE correo = ?", (hash_password(nueva_contrasena), correo))
    conn.commit()
    conn.close()
    print(f"[LOG] Contraseña actualizada para {correo}")
if "usuario" not in st.session_state:
    # Mostrar login si no hay usuarios creados
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuario_count = cursor.fetchone()[0]
    conn.close()

    if usuario_count == 0:
        st.title("🆕 Registro inicial de Superadministrador")
        with st.form("registro_inicial"):
            nombre = st.text_input("Nombre completo")
            correo = st.text_input("Correo")
            contrasena = st.text_input("Contraseña", type="password")
            confirmar = st.text_input("Confirmar contraseña", type="password")
            submitted = st.form_submit_button("Crear Superadmin")
            if submitted:
                if contrasena == confirmar:
                    crear_usuario(nombre, correo, contrasena, "superadmin", None)
                    st.success("✅ Usuario creado. Reinicia la app e inicia sesión.")
                else:
                    st.error("❌ Las contraseñas no coinciden.")
        st.stop()
    else:
        st.title("🔐 Iniciar sesión")
        recuperar = st.checkbox("¿Olvidaste tu contraseña?")
        if recuperar:
            with st.form("recuperar_password"):
                correo_reset = st.text_input("Correo registrado")
                nueva = st.text_input("Nueva contraseña", type="password")
                confirmar = st.text_input("Confirmar contraseña", type="password")
                submitted_reset = st.form_submit_button("Restablecer")
                if submitted_reset:
                    if nueva != confirmar:
                        st.error("❌ Las contraseñas no coinciden.")
                    else:
                        conn = conectar_db()
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM usuarios WHERE correo = ?", (correo_reset,))
                        existe = cursor.fetchone()
                        conn.close()
                        if existe:
                            actualizar_contrasena(correo_reset, nueva)
                            st.success("✅ Contraseña actualizada. Ahora puedes iniciar sesión.")
                        else:
                            st.error("❌ Correo no encontrado.")
        with st.form("login_form"):
            correo = st.text_input("Correo")
            contrasena = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar")
            if submitted:
                usuario = autenticar_usuario(correo, contrasena)
                if usuario:
                    st.session_state.usuario = {
                        "id": usuario[0],
                        "nombre": usuario[1],
                        "tipo": usuario[2],
                        "admin_id": usuario[3]
                    }
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas.")
        st.stop()

def ver_historial(usuario):
    print(f"[LOG] Consultando historial para usuario: {usuario['nombre']} ({usuario['tipo']})")
    conn = conectar_db()
    if usuario['tipo'] == 'superadmin':
        query = "SELECT * FROM cotizaciones ORDER BY fecha DESC"
        df = pd.read_sql_query(query, conn)
    elif usuario['tipo'] == 'admin':
        query = f"""
            SELECT * FROM cotizaciones
            WHERE usuario_id IN (
                SELECT id FROM usuarios WHERE admin_id = {usuario['id']} OR id = {usuario['id']}
            ) ORDER BY fecha DESC
        """
        df = pd.read_sql_query(query, conn)
    else:
        query = f"SELECT * FROM cotizaciones WHERE usuario_id = {usuario['id']} ORDER BY fecha DESC"
        df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"[LOG] Cotizaciones encontradas: {len(df)}")
    return df

# =================== Mensaje de bienvenida ===================
if "usuario" in st.session_state:
    st.markdown(f"## 👋 Bienvenido, **{st.session_state.usuario['nombre']}** ({st.session_state.usuario['tipo']})")
    st.markdown(f"📅 Fecha actual: **{date.today().strftime('%Y-%m-%d')}**")

    # Panel resumen
    st.markdown("---")
    st.subheader("📊 Mi resumen de cotizaciones")
    resumen_df = ver_historial(st.session_state.usuario)
    cotizaciones_hoy = resumen_df[resumen_df['fecha'] == date.today().strftime('%Y-%m-%d')]
    cotizaciones_mes = resumen_df[resumen_df['fecha'].str.startswith(date.today().strftime('%Y-%m'))]

    col1, col2, col3 = st.columns(3)
    col1.metric("Hoy", len(cotizaciones_hoy))
    col2.metric("Este mes", len(cotizaciones_mes))
    col3.metric("💰 Total Mes (USD)", f"${cotizaciones_mes['total_venta'].sum():,.2f}")



# =================== Funciones de cotizaciones ===================
def guardar_cotizacion(datos, productos_venta, productos_costo):
    print(f"[LOG] Guardando cotización para: {datos['cliente']} | Responsable: {datos['responsable']}")
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen, vigencia, condiciones_comerciales, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"],
        datos["responsable"], datos["total_venta"], datos["total_costo"],
        datos["utilidad"], datos["margen"], datos["vigencia"], datos["condiciones_comerciales"], datos["usuario_id"]
    ))
    cotizacion_id = cursor.lastrowid

    print(f"[LOG] Cotización ID generada: {cotizacion_id}")

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
    print("[LOG] Cotización guardada exitosamente")
    return cotizacion_id



# ... (resto del código sigue igual)




# ... (resto del código sigue igual)


DB_PATH = "crm_cotizaciones.sqlite"

def agregar_cliente(datos):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO clientes (
            nombre, apellido_paterno, apellido_materno, empresa, correo, telefono,
            rfc, calle, numero_exterior, numero_interior, codigo_postal,
            municipio, ciudad, estado, notas
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["nombre"], datos["apellido_paterno"], datos["apellido_materno"], datos["empresa"],
        datos["correo"], datos["telefono"], datos["rfc"], datos["calle"],
        datos["numero_exterior"], datos["numero_interior"], datos["codigo_postal"],
        datos["municipio"], datos["ciudad"], datos["estado"], datos["notas"]
    ))
    conn.commit()
    conn.close()

def mostrar_clientes():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY empresa ASC", conn)
    conn.close()
    return df

def vista_clientes():
    st.title("📇 Gestión de Clientes")

    with st.expander("➕ Agregar nuevo cliente"):
        with st.form("form_nuevo_cliente"):
            col1, col2, col3 = st.columns(3)
            nombre = col1.text_input("Nombre")
            apellido_paterno = col2.text_input("Apellido Paterno")
            apellido_materno = col3.text_input("Apellido Materno")
            empresa = st.text_input("Empresa")
            correo = st.text_input("Correo electrónico")
            telefono = st.text_input("Teléfono")

            st.markdown("**Domicilio Fiscal**")
            rfc = st.text_input("RFC")
            calle = st.text_input("Calle")
            numero_exterior = st.text_input("Número Exterior")
            numero_interior = st.text_input("Número Interior")
            codigo_postal = st.text_input("Código Postal")
            municipio = st.text_input("Municipio")
            ciudad = st.text_input("Ciudad")
            estado = st.text_input("Estado")
            notas = st.text_area("Notas", height=100)

            submitted = st.form_submit_button("Guardar cliente")
            if submitted:
                datos = {
                    "nombre": nombre,
                    "apellido_paterno": apellido_paterno,
                    "apellido_materno": apellido_materno,
                    "empresa": empresa,
                    "correo": correo,
                    "telefono": telefono,
                    "rfc": rfc,
                    "calle": calle,
                    "numero_exterior": numero_exterior,
                    "numero_interior": numero_interior,
                    "codigo_postal": codigo_postal,
                    "municipio": municipio,
                    "ciudad": ciudad,
                    "estado": estado,
                    "notas": notas
                }
                agregar_cliente(datos)
                st.success("✅ Cliente guardado con éxito")

    st.subheader("📋 Lista de Clientes")
    df = mostrar_clientes()
    st.dataframe(df)

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
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()

st.title("Cotizador ThreatDown con CRM")

menu = st.sidebar.selectbox("Secciones", ["Cotizaciones", "Clientes"])

if menu == "Clientes":
    vista_clientes()
    st.stop()


st.sidebar.header("Datos de la cotización")

# Asegurar inicialización de base de datos antes de cualquier consulta
inicializar_db()

# Cargar empresas registradas de forma segura
try:
    conn = conectar_db()
    df_clientes = pd.read_sql_query("SELECT * FROM clientes ORDER BY empresa ASC", conn)
    conn.close()
except Exception as e:
    st.error("❌ Error al cargar clientes: asegúrate de haber inicializado la base de datos y que existan datos.")
    st.stop()

if df_clientes.empty:
    st.sidebar.warning("⚠️ No hay clientes registrados. Por favor agrega uno primero en la sección 'Clientes'.")
    st.stop()


# =======================
# Cargar empresas registradas
# =======================
conn = conectar_db()
df_clientes = pd.read_sql_query("SELECT * FROM clientes ORDER BY empresa ASC", conn)
conn.close()

if df_clientes.empty:
    st.sidebar.warning("⚠️ No hay clientes registrados. Por favor agrega uno primero en la sección 'Clientes'.")
    st.stop()

empresa_seleccionada = st.sidebar.selectbox("Selecciona la empresa cliente", df_clientes["empresa"].unique())
cliente_row = df_clientes[df_clientes["empresa"] == empresa_seleccionada].iloc[0]
cliente = empresa_seleccionada
contacto = cliente_row["nombre"] + " " + cliente_row["apellido_paterno"] + " " + cliente_row["apellido_materno"]

df_clientes["display"] = df_clientes["nombre"] + " " + df_clientes["apellido_paterno"] + " " + df_clientes["apellido_materno"] + " - " + df_clientes["empresa"]
cliente_seleccionado = st.sidebar.selectbox("Selecciona un cliente", df_clientes["display"])
cliente_row = df_clientes[df_clientes["display"] == cliente_seleccionado].iloc[0]
cliente = cliente_row["empresa"]
contacto = cliente_row["nombre"] + " " + cliente_row["apellido_paterno"] + " " + cliente_row["apellido_materno"]

propuesta = st.sidebar.text_input("Nombre de la propuesta")
fecha = st.sidebar.date_input("Fecha", value=date.today())
responsable = st.sidebar.text_input("Responsable / Vendedor")

vigencia = st.text_input(
    "Vigencia de la propuesta",
    value="30 días"
)

condiciones_comerciales = st.text_area(
    "Condiciones de Pago y Comerciales",
    value="Precios en USD. Pago contra entrega. No incluye impuestos. Licenciamiento anual.",
    height=150
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
            "total_venta": precio_venta_total,
            "total_costo": costo_total,
            "utilidad": utilidad,
            "margen": margen,
        "vigencia": vigencia,
        "condiciones_comerciales": condiciones_comerciales
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

    def condiciones(self, vigencia, condiciones):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 6, f"Vigencia de la propuesta: {vigencia}\n")
        self.multi_cell(0, 6, f"{condiciones}")
        self.ln(10)

    def firma(self, responsable):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, "Atentamente,", ln=True)
        self.cell(0, 8, responsable, ln=True)
        self.cell(0, 8, "SYNAPPSSYS", ln=True)

# Botón para generar PDF desde vista de detalle
if 'cotizacion_id' in locals():
    if st.button("📄 Generar PDF para cliente"):
        pdf = CotizacionPDFConLogo()
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
        pdf.condiciones(datos["vigencia"], datos["condiciones_comerciales"])
        pdf.firma(datos["responsable"])

        pdf_output_path = f"cotizacion_cliente_{cotizacion_id}.pdf"
        pdf.output(pdf_output_path)
        with open(pdf_output_path, "rb") as file:
            st.download_button(
                label="📥 Descargar PDF de cotización",
                data=file,
                file_name=pdf_output_path,
                mime="application/pdf"
            )



DB_PATH = "crm_cotizaciones.sqlite"
