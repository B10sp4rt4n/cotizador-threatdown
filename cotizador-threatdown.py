# Cotizador ThreatDown V17 con autenticación y roles de usuario - v2 (Corregido y Limpio)

import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import os
from datetime import date
from fpdf import FPDF
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# --- Constants ---
# Use os.getcwd() to ensure the path is relative to the script location, helpful for Streamlit Cloud
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones_v2.sqlite")
LOGO_PATH = os.path.join(os.getcwd(), "LOGO Syn Apps Sys_edited (2).png") # Ensure logo is in the same dir or provide correct path
EXCEL_PATH = os.path.join(os.getcwd(), "precios_threatdown.xlsx") # Ensure excel is in the same dir

# =================== Database Functions ===================
def conectar_db():
    """Establishes connection to the SQLite database."""
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database: {e}")
        st.error(f"Error connecting to database: {e}")
        st.stop()

def inicializar_db():
    """Initializes the database and creates tables if they don't exist."""
    logging.info("Initializing database if needed...")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Usuarios Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                correo TEXT UNIQUE NOT NULL,
                contraseña TEXT NOT NULL,
                tipo_usuario TEXT CHECK(tipo_usuario IN ('superadmin', 'admin', 'user')), -- Added constraint
                admin_id INTEGER, -- ID of the admin this user reports to (if user type)
                FOREIGN KEY (admin_id) REFERENCES usuarios(id)
            )
        """)
        # Clientes Table (FIXED: Added missing table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                apellido_paterno TEXT,
                apellido_materno TEXT,
                empresa TEXT UNIQUE NOT NULL, -- Empresa should likely be unique
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
        # Cotizaciones Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, -- Consider storing client_id instead?
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
                usuario_id INTEGER NOT NULL, -- Cotization must belong to a user
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
        """)
        # Detalle Productos Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER NOT NULL,
                producto TEXT,
                cantidad INTEGER,
                precio_unitario REAL,
                precio_total REAL,
                descuento_aplicado REAL, -- This seems to store discount % for 'venta' and 'Item Disc. %' for 'costo'
                tipo_origen TEXT CHECK(tipo_origen IN ('venta', 'costo')), -- Added constraint
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id) ON DELETE CASCADE -- Added cascade delete
            )
        """)
        conn.commit()
        logging.info("Database schema checked/updated successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        st.error(f"Database initialization failed: {e}")
        st.stop() # Stop execution if DB init fails
    finally:
        if conn:
            conn.close()

# =================== Authentication Functions ===================
def hash_password(password):
    """Hashes a password using SHA256."""
    hashed = hashlib.sha256(password.encode()).hexdigest()
    # logging.info(f"Password hashed: {hashed[:5]}...") # Avoid logging full hash
    return hashed

def autenticar_usuario(correo, contrasena):
    """Authenticates a user based on email and password."""
    logging.info(f"Attempting authentication for user: {correo}")
    usuario = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, tipo_usuario, admin_id FROM usuarios
            WHERE correo = ? AND contraseña = ?
        """, (correo, hash_password(contrasena)))
        usuario = cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Error during authentication query for {correo}: {e}")
        st.error("An error occurred during login. Please try again.")
    finally:
        if conn:
            conn.close()
    if usuario:
        logging.info(f"Authentication successful for: {correo}")
        return usuario
    else:
        logging.warning(f"Authentication failed for: {correo}")
        return None

def crear_usuario(nombre, correo, contrasena, tipo_usuario, admin_id=None):
    """Creates a new user in the database."""
    logging.info(f"Creating user: {nombre}, type: {tipo_usuario}, admin_id: {admin_id}")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO usuarios (nombre, correo, contraseña, tipo_usuario, admin_id)
            VALUES (?, ?, ?, ?, ?)
        """, (nombre, correo, hash_password(contrasena), tipo_usuario, admin_id))
        conn.commit()
        logging.info(f"User {correo} created successfully.")
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"Attempted to create user with existing email: {correo}")
        st.error(f"❌ Error: El correo '{correo}' ya está registrado.")
        return False
    except sqlite3.Error as e:
        logging.error(f"Error creating user {correo}: {e}")
        st.error("Ocurrió un error al crear el usuario.")
        return False
    finally:
        if conn:
            conn.close()

def actualizar_contrasena(correo, nueva_contrasena):
    """Updates the password for a given user email."""
    logging.info(f"Updating password for user: {correo}")
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # First check if user exists
        cursor.execute("SELECT id FROM usuarios WHERE correo = ?", (correo,))
        existe = cursor.fetchone()
        if not existe:
            logging.warning(f"Password update failed: User {correo} not found.")
            st.error("❌ Correo no encontrado.")
            return False

        cursor.execute("UPDATE usuarios SET contraseña = ? WHERE correo = ?", (hash_password(nueva_contrasena), correo))
        conn.commit()
        logging.info(f"Password updated successfully for {correo}")
        return True
    except sqlite3.Error as e:
        logging.error(f"Error updating password for {correo}: {e}")
        st.error("Ocurrió un error al actualizar la contraseña.")
        return False
    finally:
        if conn:
            conn.close()

# =================== CRM (Client) Functions ===================
def agregar_cliente(datos):
    """Adds a new client to the database."""
    logging.info(f"Adding client: {datos.get('empresa', 'N/A')}")
    try:
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
            datos.get("nombre"), datos.get("apellido_paterno"), datos.get("apellido_materno"), datos.get("empresa"),
            datos.get("correo"), datos.get("telefono"), datos.get("rfc"), datos.get("calle"),
            datos.get("numero_exterior"), datos.get("numero_interior"), datos.get("codigo_postal"),
            datos.get("municipio"), datos.get("ciudad"), datos.get("estado"), datos.get("notas")
        ))
        conn.commit()
        logging.info(f"Client '{datos.get('empresa')}' added successfully.")
        return True
    except sqlite3.IntegrityError:
        logging.warning(f"Attempted to add client with existing company name: {datos.get('empresa')}")
        st.error(f"❌ Error: La empresa '{datos.get('empresa')}' ya está registrada.")
        return False
    except sqlite3.Error as e:
        logging.error(f"Error adding client {datos.get('empresa')}: {e}")
        st.error("Ocurrió un error al guardar el cliente.")
        return False
    finally:
        if conn:
            conn.close()

def mostrar_clientes():
    """Retrieves all clients from the database, ordered by company name."""
    logging.info("Fetching client list.")
    try:
        conn = conectar_db()
        df = pd.read_sql_query("SELECT * FROM clientes ORDER BY empresa ASC", conn)
        return df
    except sqlite3.Error as e:
        logging.error(f"Error fetching clients: {e}")
        st.error("Ocurrió un error al cargar los clientes.")
        return pd.DataFrame() # Return empty dataframe on error
    finally:
        if conn:
            conn.close()

def cargar_clientes_para_seleccion():
    """Loads client data specifically for dropdown selection."""
    df = mostrar_clientes()
    if not df.empty:
        df["display_contact"] = df["nombre"] + " " + df["apellido_paterno"] # Simplify display
        df["display_empresa"] = df["empresa"]
    return df

# =================== Cotizador Functions ===================
def cargar_datos_precios():
    """Loads pricing data from the Excel file."""
    logging.info(f"Loading pricing data from: {EXCEL_PATH}")
    try:
        if not os.path.exists(EXCEL_PATH):
             logging.error(f"Pricing file not found at: {EXCEL_PATH}")
             st.error(f"Error: Archivo de precios '{os.path.basename(EXCEL_PATH)}' no encontrado.")
             return pd.DataFrame() # Return empty dataframe

        df = pd.read_excel(EXCEL_PATH)
        # Ensure tier columns are numeric, coerce errors to NaN
        df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
        df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
        # Drop rows where tier conversion failed
        original_rows = len(df)
        df = df.dropna(subset=["Tier Min", "Tier Max"])
        if len(df) < original_rows:
            logging.warning(f"Removed {original_rows - len(df)} rows from pricing data due to non-numeric tiers.")
        logging.info(f"Pricing data loaded successfully: {len(df)} rows.")
        return df
    except FileNotFoundError:
        logging.error(f"Pricing file not found at: {EXCEL_PATH}")
        st.error(f"Error: Archivo de precios '{os.path.basename(EXCEL_PATH)}' no encontrado.")
        return pd.DataFrame()
    except Exception as e:
        logging.error(f"Error loading or processing pricing file: {e}")
        st.error(f"Error al cargar el archivo de precios: {e}")
        return pd.DataFrame()

def guardar_cotizacion(datos, productos_venta, productos_costo):
    """Saves a quotation and its details to the database."""
    logging.info(f"Saving quotation for: {datos.get('cliente', 'N/A')} | By User ID: {datos.get('usuario_id', 'N/A')}")
    cotizacion_id = None
    try:
        conn = conectar_db()
        cursor = conn.cursor()
        # Insert main cotizacion record
        cursor.execute("""
            INSERT INTO cotizaciones (cliente, contacto, propuesta, fecha, responsable,
                                    total_venta, total_costo, utilidad, margen, vigencia,
                                    condiciones_comerciales, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos.get("cliente"), datos.get("contacto"), datos.get("propuesta"), datos.get("fecha"),
            datos.get("responsable"), datos.get("total_venta"), datos.get("total_costo"),
            datos.get("utilidad"), datos.get("margen"), datos.get("vigencia"),
            datos.get("condiciones_comerciales"), datos.get("usuario_id")
        ))
        cotizacion_id = cursor.lastrowid
        logging.info(f"Quotation base record saved with ID: {cotizacion_id}")

        # Insert venta product details
        for p in productos_venta:
            cursor.execute("""
                INSERT INTO detalle_productos (cotizacion_id, producto, cantidad, precio_unitario, precio_total, descuento_aplicado, tipo_origen)
                VALUES (?, ?, ?, ?, ?, ?, 'venta')
            """, (
                cotizacion_id, p.get("Producto"), p.get("Cantidad"), p.get("Precio Unitario de Lista"),
                p.get("Precio Total con Descuento"), p.get("Descuento %")
            ))

        # Insert costo product details
        for p in productos_costo:
            cursor.execute("""
                INSERT INTO detalle_productos (cotizacion_id, producto, cantidad, precio_unitario, precio_total, descuento_aplicado, tipo_origen)
                VALUES (?, ?, ?, ?, ?, ?, 'costo')
            """, (
                cotizacion_id, p.get("Producto"), p.get("Cantidad"), p.get("Precio Base"), # Costo uses 'Precio Base' as unit price
                p.get("Subtotal"), p.get("Item Disc. %") # Costo uses 'Item Disc. %' as discount
            ))

        conn.commit()
        logging.info(f"Quotation {cotizacion_id} and details saved successfully.")
        return cotizacion_id
    except sqlite3.Error as e:
        logging.error(f"Error saving quotation {cotizacion_id if cotizacion_id else 'N/A'}: {e}")
        st.error("Ocurrió un error al guardar la cotización.")
        # Rollback might be needed here in a more complex scenario
        return None
    finally:
        if conn:
            conn.close()

def ver_historial(usuario):
    """Retrieves quotation history based on user role."""
    user_id = usuario['id']
    user_type = usuario['tipo']
    logging.info(f"Fetching quotation history for user: {usuario['nombre']} ({user_type})")
    query = ""
    params = ()

    try:
        conn = conectar_db()
        if user_type == 'superadmin':
            query = "SELECT id, cliente, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen FROM cotizaciones ORDER BY fecha DESC, id DESC"
        elif user_type == 'admin':
            # Admin sees their own quotes and quotes of users they manage
            query = f"""
                SELECT id, cliente, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen
                FROM cotizaciones
                WHERE usuario_id = ? OR usuario_id IN (SELECT id FROM usuarios WHERE admin_id = ?)
                ORDER BY fecha DESC, id DESC
            """
            params = (user_id, user_id)
        else: # 'user' type
            query = "SELECT id, cliente, propuesta, fecha, responsable, total_venta, total_costo, utilidad, margen FROM cotizaciones WHERE usuario_id = ? ORDER BY fecha DESC, id DESC"
            params = (user_id,)

        df = pd.read_sql_query(query, conn, params=params)
        logging.info(f"Found {len(df)} quotations for user {usuario['nombre']}")
        return df
    except sqlite3.Error as e:
        logging.error(f"Error fetching history for user {usuario['nombre']}: {e}")
        st.error("Ocurrió un error al cargar el historial de cotizaciones.")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def obtener_detalle_cotizacion(cotizacion_id):
    """Fetches full details for a specific quotation ID."""
    logging.info(f"Fetching details for quotation ID: {cotizacion_id}")
    detalles = {}
    try:
        conn = conectar_db()
        # Get main data
        datos_df = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = ?", conn, params=(cotizacion_id,))
        if datos_df.empty:
            logging.warning(f"Quotation ID {cotizacion_id} not found.")
            return None
        detalles['datos'] = datos_df.iloc[0]

        # Get venta products
        df_venta = pd.read_sql_query(f"""
            SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
            FROM detalle_productos
            WHERE cotizacion_id = ? AND tipo_origen = 'venta'
        """, conn, params=(cotizacion_id,))
        detalles['venta'] = df_venta

        # Get costo products
        df_costo = pd.read_sql_query(f"""
            SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
            FROM detalle_productos
            WHERE cotizacion_id = ? AND tipo_origen = 'costo'
        """, conn, params=(cotizacion_id,))
        detalles['costo'] = df_costo

        logging.info(f"Details fetched successfully for quotation ID: {cotizacion_id}")
        return detalles
    except sqlite3.Error as e:
        logging.error(f"Error fetching details for quotation {cotizacion_id}: {e}")
        st.error(f"Ocurrió un error al cargar el detalle de la cotización {cotizacion_id}.")
        return None
    finally:
        if conn:
            conn.close()


# =================== PDF Generation Class ===================
class CotizacionPDFConLogo(FPDF):
    def __init__(self, logo_path=LOGO_PATH, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_path = logo_path
        self.add_font('Helvetica', '', 'helvetica.ttf', uni=True) # Ensure font is available or handle fallback
        self.add_font('Helvetica', 'B', 'helvetica_bold.ttf', uni=True)
        self.set_font("Helvetica", "", 10) # Default font

    def header(self):
        try:
            if os.path.exists(self.logo_path):
                 self.image(self.logo_path, x=10, y=8, w=50)
            else:
                logging.warning(f"Logo file not found at: {self.logo_path}. Skipping logo.")
                self.set_xy(10, 10)
                self.cell(50, 10, "[Logo Ausente]", border=0) # Placeholder if logo missing
        except Exception as e:
            logging.error(f"Error loading logo in PDF: {e}")
            self.set_xy(10, 10)
            self.cell(50, 10, "[Error Logo]", border=0)

        self.set_font("Helvetica", "B", 16)
        # Position title next to logo space
        self.set_xy(70, 12)
        self.cell(0, 10, "Cotización de Servicios", ln=True, align="L", border=0)
        self.ln(20) # Space after header

    def footer(self):
        self.set_y(-15) # Position 1.5 cm from bottom
        self.set_font("Helvetica", "", 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', align='C', border=0) # Page numbering

    def encabezado_cliente(self, datos):
        self.set_font("Helvetica", "", 10)
        col_width = 95 # Half page width approx
        y_start = self.get_y()
        self.multi_cell(col_width, 6, f"Cliente: {datos.get('cliente', '')}\nContacto: {datos.get('contacto', '')}\nPropuesta: {datos.get('propuesta', '')}", border=0)
        self.set_xy(col_width + 10, y_start) # Move to the right column
        self.multi_cell(col_width, 6, f"Fecha: {datos.get('fecha', '')}\nResponsable: {datos.get('responsable', '')}", border=0)
        self.ln(5)

    def tabla_productos(self, productos_df):
        if productos_df.empty:
            self.cell(0, 10, "No hay productos en esta cotización.", ln=True)
            return

        self.set_font("Helvetica", "B", 9)
        # Define column widths - adjust as needed
        total_width = self.w - 2*self.l_margin
        col_widths = {
            "Producto": total_width * 0.40,
            "Cantidad": total_width * 0.10,
            "P. Unitario": total_width * 0.18,
            "Descuento %": total_width * 0.12,
            "Total": total_width * 0.20
        }

        # Headers
        self.cell(col_widths["Producto"], 8, "Producto", 1, align="C")
        self.cell(col_widths["Cantidad"], 8, "Cantidad", 1, align="C")
        self.cell(col_widths["P. Unitario"], 8, "P. Unitario", 1, align="C")
        self.cell(col_widths["Descuento %"], 8, "Desc. %", 1, align="C") # Abbreviated header
        self.cell(col_widths["Total"], 8, "Total", 1, ln=True, align="C")

        # Data
        self.set_font("Helvetica", "", 9)
        for _, p in productos_df.iterrows():
            # Handle potential word wrap for product name
            x_before = self.get_x()
            y_before = self.get_y()
            self.multi_cell(col_widths["Producto"], 8, str(p.get("producto", "")), 1, align="L")
            y_after = self.get_y()
            h = y_after - y_before # Calculated height of the multi_cell
            # Reset position for other cells in the same row
            self.set_xy(x_before + col_widths["Producto"], y_before)

            self.cell(col_widths["Cantidad"], h, str(p.get("cantidad", "")), 1, align="C")
            self.cell(col_widths["P. Unitario"], h, f"${p.get('precio_unitario', 0):,.2f}", 1, align="R")
            self.cell(col_widths["Descuento %"], h, f"{p.get('descuento_aplicado', 0):.2f}%", 1, align="R")
            self.cell(col_widths["Total"], h, f"${p.get('precio_total', 0):,.2f}", 1, align="R")
            self.set_xy(self.l_margin, y_after) # Move to next line start
        self.ln(5)

    def totales(self, total_venta):
        self.set_font("Helvetica", "B", 11)
        # Position total to the right
        total_width = self.w - 2*self.l_margin
        label_width = total_width * 0.80
        value_width = total_width * 0.20
        self.cell(label_width, 10, "Total de la propuesta (USD):", align="R", border=0)
        self.cell(value_width, 10, f"${total_venta:,.2f}", ln=True, align="R", border="T") # Top border for emphasis
        self.ln(8)

    def condiciones(self, vigencia, condiciones):
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 6, "Condiciones Comerciales", ln=True)
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, f"Vigencia de la propuesta: {vigencia}\n{condiciones}", border=0)
        self.ln(8)

    def firma(self, responsable):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Atentamente,", ln=True)
        self.ln(10) # Space for signature
        self.line(self.get_x(), self.get_y(), self.get_x() + 60, self.get_y()) # Signature line
        self.ln(2)
        self.cell(0, 6, responsable, ln=True)
        self.cell(0, 6, "SYNAPPSSYS", ln=True) # Company name or title

# =================== Streamlit App UI & Logic ===================

# --- Initialize Database ---
inicializar_db() # Ensure tables exist before proceeding

# --- Authentication Check ---
if "usuario" not in st.session_state:
    # Check if any users exist, if not, force Superadmin creation
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        usuario_count = cursor.fetchone()[0]
    except sqlite3.Error as e:
        logging.error(f"Failed to count users: {e}")
        st.error("Error accessing user data. Cannot proceed.")
        st.stop()
    finally:
        conn.close()

    if usuario_count == 0:
        st.title("🆕 Registro inicial de Superadministrador")
        st.warning("No hay usuarios registrados. Debe crear el primer Superadministrador.")
        with st.form("registro_inicial"):
            nombre = st.text_input("Nombre completo (*)")
            correo = st.text_input("Correo electrónico (*)")
            contrasena = st.text_input("Contraseña (*)", type="password")
            confirmar = st.text_input("Confirmar contraseña (*)", type="password")
            submitted = st.form_submit_button("Crear Superadmin")
            if submitted:
                if not all([nombre, correo, contrasena, confirmar]):
                    st.error("❌ Por favor, complete todos los campos obligatorios (*).")
                elif contrasena != confirmar:
                    st.error("❌ Las contraseñas no coinciden.")
                else:
                    if crear_usuario(nombre, correo, contrasena, "superadmin", None):
                        st.success("✅ Superadministrador creado exitosamente. Por favor, reinicia la página e inicia sesión.")
                        st.stop() # Stop execution after successful creation

    else: # Users exist, show login form
        st.title("🔐 Iniciar sesión")
        with st.form("login_form"):
            correo = st.text_input("Correo electrónico")
            contrasena = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Ingresar")
            if submitted:
                usuario_data = autenticar_usuario(correo, contrasena)
                if usuario_data:
                    st.session_state.usuario = {
                        "id": usuario_data[0],
                        "nombre": usuario_data[1],
                        "tipo": usuario_data[2],
                        "admin_id": usuario_data[3]
                    }
                    st.success("✅ Acceso concedido.")
                    st.rerun() # Rerun the script to show the main app
                else:
                    st.error("❌ Credenciales incorrectas o error de autenticación.")

        # Password Recovery Section (Optional)
        st.markdown("---")
        with st.expander("¿Olvidaste tu contraseña?"):
             with st.form("recuperar_password"):
                correo_reset = st.text_input("Correo registrado para restablecer")
                nueva = st.text_input("Nueva contraseña", type="password", key="new_pass")
                confirmar_nueva = st.text_input("Confirmar nueva contraseña", type="password", key="confirm_pass")
                submitted_reset = st.form_submit_button("Restablecer Contraseña")
                if submitted_reset:
                    if not correo_reset or not nueva or not confirmar_nueva:
                         st.warning("Por favor, complete todos los campos.")
                    elif nueva != confirmar_nueva:
                        st.error("❌ Las nuevas contraseñas no coinciden.")
                    else:
                        if actualizar_contrasena(correo_reset, nueva):
                            st.success("✅ Contraseña actualizada. Ahora puedes iniciar sesión con la nueva contraseña.")
                        # Error messages are handled within actualizar_contrasena

    # Stop execution if not logged in
    st.stop()

# --- Main Application (User is Logged In) ---
st.sidebar.image(LOGO_PATH, width=150) # Show logo in sidebar after login
st.sidebar.markdown(f"### Bienvenido, {st.session_state.usuario['nombre']}")
st.sidebar.markdown(f"Rol: **{st.session_state.usuario['tipo']}**")
if st.sidebar.button("Cerrar sesión"):
    del st.session_state.usuario
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio("Secciones", ["Dashboard", "Nueva Cotización", "Historial", "Clientes", "Gestión Usuarios"], key="main_menu")
st.sidebar.markdown("---")

# --- Dashboard View ---
if menu == "Dashboard":
    st.markdown(f"## 👋 Resumen General")
    st.markdown(f"📅 Fecha actual: **{date.today().strftime('%Y-%m-%d')}**")
    st.markdown("---")
    st.subheader("📊 Mis Cotizaciones Recientes")

    try:
        resumen_df = ver_historial(st.session_state.usuario) # Use the role-aware history function
        if not resumen_df.empty:
            resumen_df['fecha'] = pd.to_datetime(resumen_df['fecha']) # Convert to datetime for comparison
            today_str = date.today().strftime('%Y-%m-%d')
            month_start_str = date.today().strftime('%Y-%m')

            cotizaciones_hoy = resumen_df[resumen_df['fecha'].dt.strftime('%Y-%m-%d') == today_str]
            cotizaciones_mes = resumen_df[resumen_df['fecha'].dt.strftime('%Y-%m') == month_start_str]

            col1, col2, col3 = st.columns(3)
            col1.metric("Cotizaciones Hoy", len(cotizaciones_hoy))
            col2.metric("Cotizaciones Este Mes", len(cotizaciones_mes))
            col3.metric("💰 Total Vendido Mes (USD)", f"${cotizaciones_mes['total_venta'].sum():,.2f}")

            st.dataframe(resumen_df.head(10)) # Show recent 10
        else:
            st.info("Aún no has creado ninguna cotización.")
    except Exception as e:
        logging.error(f"Error displaying dashboard: {e}")
        st.error("No se pudo cargar el resumen del dashboard.")


# --- Client Management View ---
elif menu == "Clientes":
    st.title("📇 Gestión de Clientes")

    with st.expander("➕ Agregar nuevo cliente"):
        with st.form("form_nuevo_cliente", clear_on_submit=True):
            st.subheader("Información de Contacto y Empresa")
            col1, col2, col3 = st.columns(3)
            nombre = col1.text_input("Nombre")
            apellido_paterno = col2.text_input("Apellido Paterno")
            apellido_materno = col3.text_input("Apellido Materno")
            empresa = st.text_input("Empresa (*)", help="Nombre único de la empresa")
            correo = st.text_input("Correo electrónico")
            telefono = st.text_input("Teléfono")

            st.subheader("Domicilio Fiscal (Opcional)")
            rfc = st.text_input("RFC")
            col_dom1, col_dom2, col_dom3 = st.columns(3)
            calle = col_dom1.text_input("Calle")
            numero_exterior = col_dom2.text_input("Número Exterior")
            numero_interior = col_dom3.text_input("Número Interior")
            col_dom4, col_dom5, col_dom6 = st.columns(3)
            codigo_postal = col_dom4.text_input("Código Postal")
            municipio = col_dom5.text_input("Municipio")
            ciudad = col_dom6.text_input("Ciudad")
            estado = st.text_input("Estado")
            notas = st.text_area("Notas Adicionales", height=100)

            submitted = st.form_submit_button("Guardar cliente")
            if submitted:
                if not empresa:
                    st.error("❌ El campo 'Empresa' es obligatorio.")
                else:
                    datos_cliente = {
                        "nombre": nombre, "apellido_paterno": apellido_paterno, "apellido_materno": apellido_materno,
                        "empresa": empresa, "correo": correo, "telefono": telefono, "rfc": rfc, "calle": calle,
                        "numero_exterior": numero_exterior, "numero_interior": numero_interior, "codigo_postal": codigo_postal,
                        "municipio": municipio, "ciudad": ciudad, "estado": estado, "notas": notas
                    }
                    if agregar_cliente(datos_cliente):
                        st.success("✅ Cliente guardado con éxito.")
                        # No need to rerun here, the dataframe below will refresh on next interaction
                    # Error message handled by agregar_cliente

    st.subheader("📋 Lista de Clientes Registrados")
    df_clientes_mostrados = mostrar_clientes()
    if df_clientes_mostrados.empty:
        st.info("No hay clientes registrados actualmente.")
    else:
        st.dataframe(df_clientes_mostrados)


# --- New Quotation View ---
elif menu == "Nueva Cotización":
    st.title("📝 Crear Nueva Cotización")

    # --- Load prerequisite data ---
    df_precios = cargar_datos_precios()
    if df_precios.empty:
        st.error("No se pueden crear cotizaciones sin datos de precios. Verifique el archivo Excel.")
        st.stop()

    df_clientes = cargar_clientes_para_seleccion()
    if df_clientes.empty:
        st.warning("⚠️ No hay clientes registrados. Por favor, agregue uno en la sección 'Clientes' antes de cotizar.")
        st.stop()

    # --- Form for Quotation Details ---
    with st.form("cotizacion_form"):
        st.subheader("1. Datos Generales")
        col_form1, col_form2 = st.columns(2)

        # Client Selection
        empresa_seleccionada = col_form1.selectbox("Selecciona la empresa cliente (*)", df_clientes["display_empresa"].unique(), key="empresa_sel")
        cliente_row = df_clientes[df_clientes["empresa"] == empresa_seleccionada].iloc[0]
        cliente_nombre_completo = f"{cliente_row['nombre']} {cliente_row['apellido_paterno']} {cliente_row['apellido_materno']}".strip()
        contacto_display = cliente_nombre_completo if cliente_nombre_completo else cliente_row['correo'] # Fallback to email if no name
        st.info(f"Contacto principal detectado: **{contacto_display}**")

        propuesta = col_form2.text_input("Nombre de la propuesta (*)")
        fecha_cot = st.date_input("Fecha (*)", value=date.today())
        responsable = st.text_input("Responsable / Vendedor (*)", value=st.session_state.usuario['nombre']) # Default to logged in user
        vigencia = st.text_input("Vigencia de la propuesta", value="15 días")
        condiciones_comerciales = st.text_area(
            "Condiciones de Pago y Comerciales",
            value="Precios en USD más IVA. Pago anticipado. Licenciamiento anual. No incluye servicios de implementación.",
            height=120
        )

        st.subheader("2. Selección de Productos y Cantidades")
        terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique().astype(int))
        termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (meses) (*):", terminos_disponibles, key="term_sel")

        df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado].copy()
        productos_disponibles = sorted(df_filtrado_termino["Product Title"].unique())
        productos_seleccionados = st.multiselect("Selecciona los productos a cotizar (*):", productos_disponibles, key="prod_sel")

        st.subheader("3. Configuración de Precios y Descuentos")
        productos_cotizacion_costo = []
        productos_cotizacion_venta = []
        costo_total_calculado = 0.0
        venta_total_calculada = 0.0
        input_valid = True

        if not productos_seleccionados:
            st.warning("Seleccione al menos un producto.")
            input_valid = False
        else:
            # Calculate Costs (Internal View)
            st.markdown("**Cálculo de Costos (Referencia Interna)**")
            cols_costo = st.columns(5)
            cols_costo[0].markdown("**Producto**")
            cols_costo[1].markdown("**Cantidad**")
            cols_costo[2].markdown("**P. Base (USD)**")
            cols_costo[3].markdown("**Item Disc (%)**")
            cols_costo[4].markdown("**Subtotal Costo (USD)**")

            for i, prod in enumerate(productos_seleccionados):
                cols_prod_costo = st.columns(5)
                df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod]
                with cols_prod_costo[0]:
                    st.markdown(f"*{prod}*", unsafe_allow_html=True)
                with cols_prod_costo[1]:
                    cantidad = st.number_input(f"Cant.", min_value=1, value=1, step=1, key=f"qty_cost_{i}")
                with cols_prod_costo[2]:
                    df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]
                    if df_rango.empty:
                        st.error(f"No hay precio base para {cantidad} unidades.")
                        precio_base = 0
                        precio_final_unit_costo = 0
                        input_valid = False
                    else:
                        precio_base = df_rango.iloc[0]["MSRP USD"]
                        st.metric(label="", value=f"${precio_base:,.2f}")

                with cols_prod_costo[3]:
                     # Use standard discounts, make them editable if needed, here assuming fixed or zero
                     item_disc = st.number_input(f"Desc.", 0.0, 100.0, 0.0, step=0.5, key=f"item_disc_{i}", format="%.2f")
                     # Consider adding Channel/Deal Reg discounts if they vary per quote item
                     channel_disc = 0.0 # Example: Fetch from config or fixed
                     deal_reg_disc = 0.0 # Example

                # Calculate Cost Subtotal
                precio_costo_1 = precio_base * (1 - item_disc / 100.0)
                total_channel_deal_disc_perc = channel_disc + deal_reg_disc # Sum percentages directly ONLY IF applied sequentially on the SAME base, otherwise calculate iteratively
                precio_final_unit_costo = precio_costo_1 * (1 - total_channel_deal_disc_perc / 100.0) # Adjust if discs apply differently
                subtotal_costo = precio_final_unit_costo * cantidad
                costo_total_calculado += subtotal_costo

                with cols_prod_costo[4]:
                     st.metric(label="", value=f"${subtotal_costo:,.2f}")

                productos_cotizacion_costo.append({
                    "Producto": prod, "Cantidad": cantidad, "Precio Base": precio_base,
                    "Item Disc. %": item_disc, # Storing the item discount used for cost calc
                    # "Channel + Deal Disc. %": total_channel_deal_disc_perc, # Optional: store combined %
                    "Precio Final Unitario": round(precio_final_unit_costo, 2), # Cost price per unit
                    "Subtotal": round(subtotal_costo, 2) # Cost subtotal for the line
                })
                st.divider()

            # Calculate Sale Price (Client View)
            st.markdown("**Cálculo de Precio de Venta (Para Cliente)**")
            cols_venta = st.columns(5)
            cols_venta[0].markdown("**Producto**")
            cols_venta[1].markdown("**Cantidad**")
            cols_venta[2].markdown("**P. Lista Unit. (USD)**")
            cols_venta[3].markdown("**Desc. Venta (%)**")
            cols_venta[4].markdown("**Subtotal Venta (USD)**")

            for i, prod in enumerate(productos_seleccionados):
                # Find corresponding cost item to get quantity and list price
                cost_item = next((item for item in productos_cotizacion_costo if item["Producto"] == prod), None)
                if not cost_item: continue # Should not happen if loops are aligned

                cols_prod_venta = st.columns(5)
                with cols_prod_venta[0]:
                     st.markdown(f"*{prod}*", unsafe_allow_html=True)
                with cols_prod_venta[1]:
                     st.metric(label="", value=f"{cost_item['Cantidad']}") # Quantity from cost input
                with cols_prod_venta[2]:
                     precio_unitario_lista = cost_item['Precio Base'] # Use MSRP as list price
                     st.metric(label="", value=f"${precio_unitario_lista:,.2f}")

                with cols_prod_venta[3]:
                     # Direct discount on List Price for the client
                     descuento_venta_directo = st.number_input(f"Desc.", 0.0, 100.0, 0.0, step=0.5, key=f"venta_disc_{i}", format="%.2f")

                # Calculate Sale Subtotal
                precio_total_lista_linea = precio_unitario_lista * cost_item['Cantidad']
                precio_con_descuento_venta = precio_total_lista_linea * (1 - descuento_venta_directo / 100.0)
                venta_total_calculada += precio_con_descuento_venta

                with cols_prod_venta[4]:
                    st.metric(label="", value=f"${precio_con_descuento_venta:,.2f}")

                productos_cotizacion_venta.append({
                    "Producto": prod,
                    "Cantidad": cost_item['Cantidad'],
                    "Precio Unitario de Lista": round(precio_unitario_lista, 2),
                    "Precio Total de Lista": round(precio_total_lista_linea, 2), # For reference maybe
                    "Descuento %": descuento_venta_directo, # The discount applied for sale
                    "Precio Total con Descuento": round(precio_con_descuento_venta, 2) # Sale subtotal for the line
                })
                st.divider()

        # --- Summary and Submit ---
        st.subheader("4. Resumen y Guardar")
        if venta_total_calculada > 0 and input_valid:
            utilidad_calculada = venta_total_calculada - costo_total_calculado
            margen_calculado = (utilidad_calculada / venta_total_calculada) * 100 if venta_total_calculada else 0

            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            col_res1.metric("Costo Total Estimado", f"${costo_total_calculado:,.2f}")
            col_res2.metric("Venta Total (Cliente)", f"${venta_total_calculada:,.2f}")
            col_res3.metric("Utilidad Estimada", f"${utilidad_calculada:,.2f}")
            col_res4.metric("Margen Estimado", f"{margen_calculado:.2f}%",
                           delta=f"{margen_calculado - 15:.2f}%" if margen_calculado < 15 else None, # Example: Highlight low margin
                           delta_color="inverse") # Red if below threshold
        else:
            st.warning("Complete la selección y configuración de productos para ver el resumen.")

        submitted_cot = st.form_submit_button("💾 Guardar Cotización")
        if submitted_cot:
            # Final validation before saving
            if not all([empresa_seleccionada, propuesta, fecha_cot, responsable, termino_seleccionado, productos_seleccionados]) or not input_valid:
                 st.error("❌ Faltan datos obligatorios (*) o hay errores en la configuración de precios. Revise el formulario.")
            elif venta_total_calculada <= 0:
                 st.error("❌ El total de la venta no puede ser cero o negativo.")
            else:
                datos_guardar = {
                    "cliente": empresa_seleccionada,
                    "contacto": contacto_display,
                    "propuesta": propuesta,
                    "fecha": fecha_cot.strftime('%Y-%m-%d'),
                    "responsable": responsable,
                    "total_venta": venta_total_calculada,
                    "total_costo": costo_total_calculado,
                    "utilidad": utilidad_calculada,
                    "margen": margen_calculado,
                    "vigencia": vigencia,
                    "condiciones_comerciales": condiciones_comerciales,
                    "usuario_id": st.session_state.usuario['id'] # Link to logged in user
                }

                cot_id = guardar_cotizacion(datos_guardar, productos_cotizacion_venta, productos_cotizacion_costo)
                if cot_id:
                    st.success(f"✅ Cotización #{cot_id} guardada exitosamente.")
                    # Optionally clear form or redirect/update state
                    # st.experimental_rerun() # Could rerun to clear form
                else:
                    st.error("❌ Hubo un problema al guardar la cotización en la base de datos.")


# --- History View ---
elif menu == "Historial":
    st.title("📋 Historial de Cotizaciones")
    df_hist = ver_historial(st.session_state.usuario) # Use role-aware history function

    if df_hist.empty:
        st.info("No hay cotizaciones guardadas para mostrar.")
    else:
        st.dataframe(df_hist)

        st.subheader("🔍 Ver Detalle y Generar PDF")
        # Selectbox to choose a quote from the history table
        cotizacion_id_seleccionada = st.selectbox(
            "Selecciona el ID de una cotización para ver detalles:",
            options=[""] + list(df_hist['id'].unique()),
            format_func=lambda x: f"Cotización #{x}" if x else "Seleccionar..."
        )

        if cotizacion_id_seleccionada:
            detalles_cot = obtener_detalle_cotizacion(cotizacion_id_seleccionada)

            if detalles_cot:
                datos = detalles_cot['datos']
                df_venta_det = detalles_cot['venta']
                df_costo_det = detalles_cot['costo']

                st.markdown("---")
                st.markdown(f"### Detalle Cotización #{cotizacion_id_seleccionada}")
                # Display general data in columns
                col_det1, col_det2 = st.columns(2)
                col_det1.markdown(f"**Cliente:** {datos['cliente']}")
                col_det1.markdown(f"**Contacto:** {datos['contacto']}")
                col_det1.markdown(f"**Propuesta:** {datos['propuesta']}")
                col_det2.markdown(f"**Fecha:** {datos['fecha']}")
                col_det2.markdown(f"**Responsable:** {datos['responsable']}")
                col_det2.markdown(f"**Vigencia:** {datos['vigencia']}")

                st.markdown("**Resumen Financiero:**")
                col_fin1, col_fin2, col_fin3, col_fin4 = st.columns(4)
                col_fin1.metric("Total Venta", f"${datos['total_venta']:,.2f}")
                col_fin2.metric("Total Costo", f"${datos['total_costo']:,.2f}")
                col_fin3.metric("Utilidad", f"${datos['utilidad']:,.2f}")
                col_fin4.metric("Margen", f"{datos['margen']:.2f}%")

                st.markdown(f"**Condiciones Comerciales:** \n{datos['condiciones_comerciales']}")

                st.markdown("#### Productos Cotizados (Precio Cliente)")
                st.dataframe(df_venta_det)

                # Optionally show cost breakdown (maybe only for admin/superadmin?)
                if st.session_state.usuario['tipo'] in ['admin', 'superadmin']:
                    with st.expander("Ver desglose de costos (interno)"):
                         st.markdown("#### Productos Base (Costos Internos)")
                         st.dataframe(df_costo_det)

                # --- PDF Generation Button ---
                st.markdown("---")
                if st.button(f"📄 Generar PDF para Cliente (Cotización #{cotizacion_id_seleccionada})"):
                    with st.spinner("Generando PDF..."):
                        try:
                            pdf = CotizacionPDFConLogo()
                            pdf.set_auto_page_break(auto=True, margin=15)
                            pdf.set_title(f"Cotizacion {datos['propuesta']}")
                            pdf.set_author(datos['responsable'])
                            pdf.alias_nb_pages() # Enable page numbering {nb}
                            pdf.add_page()

                            datos_dict_pdf = datos.to_dict() # Convert Series to dict for PDF functions

                            pdf.encabezado_cliente(datos_dict_pdf)
                            pdf.tabla_productos(df_venta_det) # Use venta dataframe for client PDF
                            pdf.totales(datos['total_venta'])
                            pdf.condiciones(datos['vigencia'], datos['condiciones_comerciales'])
                            pdf.firma(datos['responsable'])

                            pdf_output_path = f"Cotizacion_{datos['cliente'].replace(' ','_')}_{cotizacion_id_seleccionada}.pdf"
                            pdf_bytes = pdf.output(dest='S').encode('latin-1') # Output as bytes

                            st.download_button(
                                label="📥 Descargar PDF de Cotización",
                                data=pdf_bytes,
                                file_name=pdf_output_path,
                                mime="application/pdf"
                            )
                            logging.info(f"PDF generated successfully for Cotizacion {cotizacion_id_seleccionada}")

                        except Exception as e:
                            logging.error(f"Error generating PDF for {cotizacion_id_seleccionada}: {e}")
                            st.error(f"Error al generar el PDF: {e}")

            else:
                st.error(f"No se pudieron cargar los detalles para la cotización {cotizacion_id_seleccionada}.")


# --- User Management View (Placeholder/Basic Example) ---
elif menu == "Gestión Usuarios":
    st.title("👥 Gestión de Usuarios")
    if st.session_state.usuario['tipo'] not in ['superadmin', 'admin']:
        st.warning("⛔ Acceso denegado. Solo administradores pueden gestionar usuarios.")
        st.stop()

    # Add functionality here: list users, add new users (admin creates users, superadmin creates admins/users)
    st.info("Funcionalidad de gestión de usuarios en desarrollo.")
    # Example: Allow superadmin/admin to create new users
    if st.session_state.usuario['tipo'] in ['superadmin', 'admin']:
         with st.expander("➕ Crear Nuevo Usuario"):
              with st.form("form_nuevo_usuario", clear_on_submit=True):
                    nombre_nuevo = st.text_input("Nombre Completo (*)")
                    correo_nuevo = st.text_input("Correo Electrónico (*)")
                    contrasena_nueva = st.text_input("Contraseña Temporal (*)", type="password")
                    confirmar_nueva = st.text_input("Confirmar Contraseña (*)", type="password")

                    if st.session_state.usuario['tipo'] == 'superadmin':
                         tipo_nuevo = st.selectbox("Tipo de Usuario (*)", ['admin', 'user'])
                         admin_asignado_id = None # Superadmin doesn't assign admin_id here directly
                    else: # Admin creating a user
                         tipo_nuevo = 'user'
                         admin_asignado_id = st.session_state.usuario['id'] # Assign the current admin
                         st.text(f"Usuario reportará a: {st.session_state.usuario['nombre']}")


                    submitted_usr = st.form_submit_button("Crear Usuario")
                    if submitted_usr:
                         if not all([nombre_nuevo, correo_nuevo, contrasena_nueva, confirmar_nueva, tipo_nuevo]):
                              st.error("❌ Complete todos los campos obligatorios (*).")
                         elif contrasena_nueva != confirmar_nueva:
                              st.error("❌ Las contraseñas no coinciden.")
                         else:
                              if crear_usuario(nombre_nuevo, correo_nuevo, contrasena_nueva, tipo_nuevo, admin_asignado_id):
                                   st.success(f"✅ Usuario '{correo_nuevo}' creado con éxito.")
                              # Error handled by crear_usuario


    # Display users (example - needs refinement for roles)
    st.subheader("👤 Usuarios Registrados")
    try:
        conn = conectar_db()
        if st.session_state.usuario['tipo'] == 'superadmin':
            df_users = pd.read_sql_query("SELECT id, nombre, correo, tipo_usuario, admin_id FROM usuarios", conn)
        elif st.session_state.usuario['tipo'] == 'admin':
             # Admin sees themselves and users they manage
             df_users = pd.read_sql_query("SELECT id, nombre, correo, tipo_usuario, admin_id FROM usuarios WHERE id = ? OR admin_id = ?", conn, params=(st.session_state.usuario['id'], st.session_state.usuario['id']))
        else: # Regular user shouldn't see this list
             df_users = pd.DataFrame()

        st.dataframe(df_users)
    except Exception as e:
        st.error(f"Error al cargar usuarios: {e}")
    finally:
        if conn: conn.close()


# --- Fallback for unknown menu option ---
else:
    st.error("Opción de menú no reconocida.")
