import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
# Asumiendo que clientes_module.py existe y funciona
# from clientes_module import vista_clientes
from fpdf import FPDF
import uuid # Para generar IDs únicos para productos manuales

# --- Configuración Inicial ---
# Crear ruta segura para base de datos en entorno escribible
APP_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else os.getcwd()
DB_PATH = os.path.join(APP_DIR, "crm_cotizaciones.sqlite")


# --- Funciones de Base de Datos ---
def inicializar_db():
    # ... (código de inicializar_db como lo tenías) ...
    pass # Placeholder si copias solo este fragmento

def conectar_db():
    # ... (código de conectar_db) ...
    pass # Placeholder

def guardar_cotizacion(datos_generales, productos_venta_final, productos_costo_final):
     # ... (código de guardar_cotizacion) ...
     pass # Placeholder

def ver_historial():
     # ... (código de ver_historial) ...
     pass # Placeholder


# --- Carga de Datos de Precios --- <<<< ¡¡¡AÑADIR ESTO DE NUEVO!!!
@st.cache_data
def cargar_datos(file_path="precios_threatdown.xlsx"):
    """Carga y procesa el archivo Excel de precios."""
    try:
        # Asegúrate que el path sea correcto relativo a la app en Cloud
        full_file_path = os.path.join(APP_DIR, file_path)
        if not os.path.exists(full_file_path):
             st.error(f"❌ Error: No se encontró el archivo de precios en la ruta esperada: '{full_file_path}'. Asegúrate de que esté incluido en tu repositorio y despliegue.")
             return pd.DataFrame()

        df = pd.read_excel(full_file_path)
        # Limpieza básica
        df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
        df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
        # Asegurar que columnas clave existan
        required_cols = ["Term (Month)", "Product Title", "MSRP USD", "Tier Min", "Tier Max"]
        if not all(col in df.columns for col in required_cols):
            st.error(f"El archivo Excel '{file_path}' debe contener las columnas: {', '.join(required_cols)}")
            return pd.DataFrame() # Retornar DF vacío si faltan columnas
        return df.dropna(subset=["Tier Min", "Tier Max", "MSRP USD"])
    except FileNotFoundError:
        # Este error es menos probable ahora con la comprobación explícita de os.path.exists
        st.error(f"❌ Error interno (FileNotFound): No se encontró el archivo de precios '{full_file_path}'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error al cargar o procesar el archivo Excel '{file_path}': {e}")
        import traceback
        st.error(traceback.format_exc()) # Muestra más detalles del error
        return pd.DataFrame()

# --- Inicializar DB y Cargar Datos ---
st.write(f"DEBUG: Directorio App: {APP_DIR}") # Mensaje de depuración
st.write(f"DEBUG: Ruta DB: {DB_PATH}")
try:
    st.write("DEBUG: Intentando inicializar DB...")
    inicializar_db()
    st.write("DEBUG: DB inicializada.")
except Exception as e:
    st.error(f"Fallo crítico al inicializar la base de datos. La aplicación no puede continuar.")
    st.exception(e) # Muestra el traceback completo en la app
    st.stop() # Detiene la ejecución si la DB falla

st.write("DEBUG: Intentando cargar datos de precios...")
# --- LLAMADA ÚNICA Y CORRECTA ---
df_precios = cargar_datos() # <--- Llamada aquí
st.write(f"DEBUG: Datos cargados. df_precios es None? {df_precios is None}. Filas: {len(df_precios) if df_precios is not None else 'N/A'}")

# --- QUITAR LA LLAMADA DUPLICADA ---
# df_precios = cargar_datos() # <<<--- ELIMINA ESTA LÍNEA

# --- Inicializar Session State para Productos Manuales ---
if 'manual_products' not in st.session_state:
    st.session_state.manual_products = []

# ... (El resto de tu código de Streamlit: UI, lógica, etc.) ...


# --- El resto de tu código (incluyendo la llamada a inicializar_db() al principio) ---
# ... (código anterior) ...

# --- Inicializar DB y Cargar Datos ---
try:
    inicializar_db()
except Exception as e:
    st.error(f"Fallo crítico al inicializar la base de datos. La aplicación no puede continuar.")
    st.exception(e) # Muestra el traceback completo en la app
    st.stop() # Detiene la ejecución si la DB falla

df_precios = cargar_datos()

# ... (resto del código) ...

df_precios = cargar_datos()

# --- Inicializar Session State para Productos Manuales ---
if 'manual_products' not in st.session_state:
    st.session_state.manual_products = [] # Lista para guardar dicts de productos manuales

# --- Interfaz de Streamlit ---
st.set_page_config(layout="wide") # Usar layout ancho
st.title("Cotizador ThreatDown con CRM")

# --- Menú Lateral ---
menu = st.sidebar.selectbox("Secciones", ["Cotizaciones", "Clientes"])

if menu == "Clientes":
    # Comenta o descomenta según tengas el módulo
    # vista_clientes()
    st.info("Funcionalidad de Clientes (comentada en el código).")
    st.stop()

# --- Entradas Generales de la Cotización (Sidebar) ---
st.sidebar.header("Datos Generales")
cliente = st.sidebar.text_input("Cliente (*)", key="cliente")
contacto = st.sidebar.text_input("Nombre de contacto", key="contacto")
propuesta = st.sidebar.text_input("Nombre de la propuesta (*)", key="propuesta")
fecha = st.sidebar.date_input("Fecha", value=date.today(), key="fecha")
responsable = st.sidebar.text_input("Responsable / Vendedor (*)", key="responsable")
vigencia = st.sidebar.text_input(
    "Vigencia",
    value="30 días",
    key="vigencia"
)
condiciones_comerciales = st.sidebar.text_area(
    "Condiciones Comerciales",
    value="Precios en USD. Pago contra entrega. No incluye impuestos. Licenciamiento anual.",
    height=100,
    key="condiciones"
)

# --- Selección de Productos del Excel ---
st.header("1. Selección de Productos (desde Lista de Precios)")

if df_precios.empty:
    st.error("No se pudieron cargar los datos de precios. Verifica el archivo Excel y las columnas requeridas.")
    st.stop() # Detener si no hay datos de precios

terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
if not terminos_disponibles:
     st.warning("No hay plazos (Term (Month)) disponibles en el archivo de precios.")
     st.stop()

termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (meses):", terminos_disponibles, key="term")

# Filtrar productos disponibles para el término seleccionado
df_filtrado_termino = df_precios[df_precios["Term (Month)"] == termino_seleccionado]
productos_disponibles = sorted(df_filtrado_termino["Product Title"].unique())

if not productos_disponibles:
    st.warning(f"No hay productos definidos para el plazo de {termino_seleccionado} meses.")
    seleccion_excel = [] # Lista vacía si no hay productos
else:
    seleccion_excel = st.multiselect(
        "Selecciona productos:",
        productos_disponibles,
        key="seleccion_excel"
    )

# --- Sección para Agregar Productos Manualmente ---
st.header("2. Agregar Productos Manualmente (Opcional)")

if st.button("➕ Agregar Producto Manual", key="add_manual"):
    # Añade un nuevo diccionario vacío con un ID único para identificarlo
    st.session_state.manual_products.append({"id": str(uuid.uuid4())})
    # st.rerun() # No siempre es necesario, Streamlit maneja bien los updates

# Mostrar inputs para cada producto manual en la lista de session_state
indices_manuales_a_eliminar = []
for i, prod_manual in enumerate(st.session_state.manual_products):
    st.markdown(f"--- \n**Producto Manual #{i+1}**")
    prod_id = prod_manual["id"] # Usar el ID único en las keys

    # Usar columnas para mejor layout
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        prod_manual["Producto"] = st.text_input("Nombre del Producto (*)", key=f"manual_nombre_{prod_id}")
        # prod_manual["Descripcion"] = st.text_area("Descripción (Opcional)", key=f"manual_desc_{prod_id}")
    with col2:
        prod_manual["Cantidad"] = st.number_input("Cantidad (*)", min_value=1, value=1, step=1, key=f"manual_cantidad_{prod_id}")
    with col3:
        # Botón para eliminar este producto manual
        if st.button(f"➖ Eliminar #{i+1}", key=f"manual_remove_{prod_id}"):
            indices_manuales_a_eliminar.append(i)

    st.markdown("**Costos y Descuentos Base:**")
    col_costo1, col_costo2, col_costo3, col_costo4 = st.columns(4)
    with col_costo1:
        prod_manual["Precio Base"] = st.number_input("Precio Base Unitario (*)", min_value=0.0, value=0.0, step=0.01, format="%.2f", key=f"manual_precio_base_{prod_id}")
    with col_costo2:
        prod_manual["Item Disc. %"] = st.number_input("Item Disc. (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"manual_item_disc_{prod_id}")
    with col_costo3:
        prod_manual["Channel Disc. %"] = st.number_input("Channel Disc. (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"manual_channel_disc_{prod_id}")
    with col_costo4:
        prod_manual["Deal Reg. Disc. %"] = st.number_input("Deal Reg. Disc. (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"manual_deal_disc_{prod_id}")

    st.markdown("**Precio de Venta:**")
    col_venta1, col_venta2 = st.columns(2)
    with col_venta1:
        # Usamos el Precio Base como Precio de Lista para el producto manual
        st.text(f"Precio Unitario Lista: ${prod_manual.get('Precio Base', 0.0):,.2f}")
        prod_manual["Precio Unitario de Lista"] = prod_manual.get("Precio Base", 0.0)
    with col_venta2:
        prod_manual["Descuento %"] = st.number_input("Descuento Directo Venta (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"manual_direct_disc_{prod_id}")

# Eliminar productos manuales marcados (iterar en reversa para no afectar índices)
if indices_manuales_a_eliminar:
    for index in sorted(indices_manuales_a_eliminar, reverse=True):
        del st.session_state.manual_products[index]
    st.rerun() # Forzar actualización de la UI después de eliminar

# --- Procesamiento y Cálculo de la Cotización ---
st.header("3. Resumen y Cálculo")

productos_costo_calculado = []
productos_venta_base = [] # Lista base para luego aplicar descuento de venta

# Procesar productos seleccionados del Excel
for prod_nombre in seleccion_excel:
    df_producto = df_filtrado_termino[df_filtrado_termino["Product Title"] == prod_nombre]
    if df_producto.empty:
        st.warning(f"No se encontró el producto '{prod_nombre}' para el plazo {termino_seleccionado}. Omitiendo.")
        continue

    # Usar un expander para los inputs de cantidad/descuentos de productos Excel
    with st.expander(f"Detalles para: {prod_nombre}"):
        cantidad = st.number_input(f"Cantidad:", min_value=1, value=1, step=1, key=f"qty_{prod_nombre}")

        # Encontrar el rango de precios correcto
        df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]

        if not df_rango.empty:
            fila = df_rango.iloc[0]
            precio_base = fila["MSRP USD"]

            st.markdown("**Costos y Descuentos Base:**")
            col_costo_excel1, col_costo_excel2, col_costo_excel3 = st.columns(3)
            with col_costo_excel1:
                 item_disc = st.number_input(f"Item Disc. (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"item_disc_{prod_nombre}")
            with col_costo_excel2:
                 channel_disc = st.number_input(f"Channel Disc. (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"channel_disc_{prod_nombre}")
            with col_costo_excel3:
                 deal_reg_disc = st.number_input(f"Deal Reg. Disc. (%)", 0.0, 100.0, 0.0, step=0.1, format="%.1f", key=f"deal_disc_{prod_nombre}")

            # Calcular Costo
            precio_costo_1 = precio_base * (1 - item_disc / 100)
            total_channel_deal = channel_disc + deal_reg_disc # Suma simple, ajustar si es multiplicativo
            precio_costo_final_unitario = precio_costo_1 * (1 - total_channel_deal / 100)
            subtotal_costo = precio_costo_final_unitario * cantidad

            productos_costo_calculado.append({
                "Producto": prod_nombre,
                "Cantidad": cantidad,
                "Precio Base": precio_base,
                "Item Disc. %": item_disc,
                "Channel + Deal Disc. %": total_channel_deal,
                "Precio Final Unitario (Costo)": round(precio_costo_final_unitario, 2),
                "Subtotal": round(subtotal_costo, 2)
            })

            # Preparar para la tabla de Venta (usamos el MSRP como precio de lista)
            st.markdown("**Precio de Venta:**")
            col_venta_excel1, col_venta_excel2 = st.columns(2)
            with col_venta_excel1:
                 st.text(f"Precio Unitario Lista: ${precio_base:,.2f}")
            with col_venta_excel2:
                 descuento_directo_venta = st.number_input(f"Descuento Directo Venta (%)",
                                                    0.0, 100.0, 0.0, step=0.1, format="%.1f",
                                                    key=f"direct_discount_{prod_nombre}")

            productos_venta_base.append({
                "Producto": prod_nombre,
                "Cantidad": cantidad,
                "Precio Unitario de Lista": precio_base,
                "Descuento %": descuento_directo_venta # Guardamos el descuento para calcular después
            })

        else:
            st.warning(f"No se encontró un rango de precios para '{prod_nombre}' con cantidad {cantidad}.")

# Procesar productos manuales (ya tienen sus inputs)
for prod_manual in st.session_state.manual_products:
    # Validar que los campos necesarios del producto manual estén llenos
    if not prod_manual.get("Producto") or prod_manual.get("Cantidad") is None or prod_manual.get("Precio Base") is None:
        st.warning(f"Faltan datos obligatorios (*) para el producto manual ID: {prod_manual['id']}. Se omitirá.")
        continue

    cantidad = prod_manual["Cantidad"]
    precio_base = prod_manual["Precio Base"]
    item_disc = prod_manual.get("Item Disc. %", 0.0)
    channel_disc = prod_manual.get("Channel Disc. %", 0.0)
    deal_reg_disc = prod_manual.get("Deal Reg. Disc. %", 0.0)
    descuento_directo_venta = prod_manual.get("Descuento %", 0.0)

    # Calcular Costo para producto manual
    precio_costo_1 = precio_base * (1 - item_disc / 100)
    total_channel_deal = channel_disc + deal_reg_disc
    precio_costo_final_unitario = precio_costo_1 * (1 - total_channel_deal / 100)
    subtotal_costo = precio_costo_final_unitario * cantidad

    productos_costo_calculado.append({
        "Producto": prod_manual["Producto"],
        "Cantidad": cantidad,
        "Precio Base": precio_base,
        "Item Disc. %": item_disc,
        "Channel + Deal Disc. %": total_channel_deal,
        "Precio Final Unitario (Costo)": round(precio_costo_final_unitario, 2),
        "Subtotal": round(subtotal_costo, 2)
    })

    # Añadir a la base para cálculo de venta
    productos_venta_base.append({
        "Producto": prod_manual["Producto"],
        "Cantidad": cantidad,
        "Precio Unitario de Lista": precio_base, # Usamos el precio base manual como lista
        "Descuento %": descuento_directo_venta
    })

# --- Mostrar Resúmenes y Calcular Totales ---
costo_total_final = 0.0
df_cotizacion_costo = pd.DataFrame() # Inicializar vacío

if productos_costo_calculado:
    st.subheader("Resumen de Costos (Estimado)")
    df_cotizacion_costo = pd.DataFrame(productos_costo_calculado)
    # Reordenar/Seleccionar columnas para mostrar
    cols_mostrar_costo = ["Producto", "Cantidad", "Precio Base", "Item Disc. %", "Channel + Deal Disc. %", "Precio Final Unitario (Costo)", "Subtotal"]
    st.dataframe(df_cotizacion_costo[cols_mostrar_costo])
    costo_total_final = df_cotizacion_costo["Subtotal"].sum()
    st.metric("Costo Total Estimado", f"${costo_total_final:,.2f}")
else:
    st.info("No hay productos seleccionados o válidos para calcular costos.")

# Calcular y mostrar tabla de VENTA FINAL
precio_venta_total_final = 0.0
productos_venta_final_calculado = []
df_tabla_venta_final = pd.DataFrame() # Inicializar vacío

if productos_venta_base:
    st.subheader("Resumen de Venta (Precio Cliente)")
    for item in productos_venta_base:
        cantidad = item["Cantidad"]
        precio_unitario_lista = item["Precio Unitario de Lista"]
        descuento_directo = item["Descuento %"]

        precio_total_lista = precio_unitario_lista * cantidad
        precio_total_con_descuento = precio_total_lista * (1 - descuento_directo / 100)

        productos_venta_final_calculado.append({
            "Producto": item["Producto"],
            "Cantidad": cantidad,
            "Precio Unitario de Lista": round(precio_unitario_lista, 2),
            "Precio Total de Lista": round(precio_total_lista, 2),
            "Descuento %": descuento_directo,
            "Precio Total con Descuento": round(precio_total_con_descuento, 2)
        })

    if productos_venta_final_calculado:
        df_tabla_venta_final = pd.DataFrame(productos_venta_final_calculado)
        # Reordenar/Seleccionar columnas para mostrar
        cols_mostrar_venta = ["Producto", "Cantidad", "Precio Unitario de Lista", "Precio Total de Lista", "Descuento %", "Precio Total con Descuento"]
        st.dataframe(df_tabla_venta_final[cols_mostrar_venta])
        precio_venta_total_final = df_tabla_venta_final["Precio Total con Descuento"].sum()
        st.metric("Precio Total de Venta (Cliente)", f"${precio_venta_total_final:,.2f}")

else:
    st.info("No hay productos válidos para calcular el precio de venta.")


# Calcular Utilidad y Margen
utilidad = 0.0
margen = 0.0
if precio_venta_total_final > 0: # Evitar división por cero
    utilidad = precio_venta_total_final - costo_total_final
    margen = (utilidad / precio_venta_total_final) * 100 if precio_venta_total_final else 0
    st.subheader("Rentabilidad de la Operación")
    col1, col2 = st.columns(2)
    col1.metric("Utilidad Estimada", f"${utilidad:,.2f}")
    col2.metric("Margen Estimado (%)", f"{margen:.2f}%")
elif costo_total_final > 0:
     st.warning("El precio de venta es cero o negativo, no se puede calcular margen.")


# --- Botón Guardar ---
st.divider()
if st.button("💾 Guardar Cotización", key="save_quote", type="primary", disabled=(not productos_venta_final_calculado)): # Deshabilitar si no hay productos
    datos_generales = {
        "cliente": cliente,
        "contacto": contacto,
        "propuesta": propuesta,
        "fecha": fecha.strftime('%Y-%m-%d'),
        "responsable": responsable,
        "total_venta": precio_venta_total_final,
        "total_costo": costo_total_final,
        "utilidad": utilidad,
        "margen": margen,
        "vigencia": vigencia,
        "condiciones_comerciales": condiciones_comerciales
    }
    # Pasar los dataframes convertidos a lista de diccionarios
    guardar_cotizacion(datos_generales,
                       df_tabla_venta_final.to_dict("records") if not df_tabla_venta_final.empty else [],
                       df_cotizacion_costo.to_dict("records") if not df_cotizacion_costo.empty else [])


# --- Historial y Detalle ---
st.divider()
st.header("📋 Historial y Detalle de Cotizaciones")

# --- Ver Historial ---
try:
    df_hist = ver_historial()
    if not df_hist.empty:
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.info("No hay cotizaciones guardadas aún.")
except Exception as e:
    st.error(f"Error al mostrar el historial: {e}")

# --- Ver Detalle de Cotización Seleccionada ---
st.subheader("🔍 Ver Detalle de Cotización")
cotizacion_id_seleccionada = None # Para usar en la generación del PDF
try:
    conn = conectar_db()
    df_cotizaciones_list = pd.read_sql_query("SELECT id, propuesta, cliente, fecha FROM cotizaciones ORDER BY fecha DESC, id DESC", conn)

    if df_cotizaciones_list.empty:
        st.info("No hay cotizaciones guardadas para mostrar detalle.")
    else:
        # Crear opción legible para el selectbox
        df_cotizaciones_list["Resumen"] = df_cotizaciones_list["id"].astype(str) + " | " + df_cotizaciones_list["fecha"] + " | " + df_cotizaciones_list["cliente"] + " | " + df_cotizaciones_list["propuesta"]
        opciones_resumen = ["Selecciona una cotización..."] + df_cotizaciones_list["Resumen"].tolist()
        seleccion_resumen = st.selectbox("Cotización:", opciones_resumen, key="select_detail")

        if seleccion_resumen != "Selecciona una cotización...":
            # Extraer ID de la cadena seleccionada
            cotizacion_id_seleccionada = int(seleccion_resumen.split(" | ")[0])

            # Datos generales
            datos_detalle = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {cotizacion_id_seleccionada}", conn).iloc[0]

            st.markdown(f"**ID:** {datos_detalle['id']}")
            st.markdown(f"**Cliente:** {datos_detalle['cliente']} | **Contacto:** {datos_detalle['contacto']}")
            st.markdown(f"**Propuesta:** {datos_detalle['propuesta']} | **Fecha:** {datos_detalle['fecha']}")
            st.markdown(f"**Responsable:** {datos_detalle['responsable']}")
            st.markdown(f"**Vigencia:** {datos_detalle['vigencia']}")

            st.text_area("Condiciones Comerciales:", value=datos_detalle['condiciones_comerciales'], height=100, disabled=True)

            col_det1, col_det2, col_det3, col_det4 = st.columns(4)
            col_det1.metric("Total Venta", f"${datos_detalle['total_venta']:,.2f}")
            col_det2.metric("Total Costo", f"${datos_detalle['total_costo']:,.2f}")
            col_det3.metric("Utilidad", f"${datos_detalle['utilidad']:,.2f}")
            col_det4.metric("Margen", f"{datos_detalle['margen']:.2f}%")


            # Productos de venta (lo que ve el cliente)
            st.markdown("##### Productos Cotizados (Venta Cliente)")
            df_venta_detalle = pd.read_sql_query(f"""
                SELECT producto AS "Producto",
                       cantidad AS "Cantidad",
                       precio_unitario AS "Precio Unit. Lista",
                       (precio_unitario * cantidad) AS "Precio Total Lista", -- Calculado al vuelo
                       descuento_aplicado AS "Desc. %",
                       precio_total AS "Precio Final"
                FROM detalle_productos
                WHERE cotizacion_id = {cotizacion_id_seleccionada} AND tipo_origen = 'venta'
            """, conn)
            st.dataframe(df_venta_detalle, use_container_width=True)

            # Productos de costo (interno)
            st.markdown("##### Detalle de Costos (Interno)")
            df_costo_detalle = pd.read_sql_query(f"""
                SELECT producto AS "Producto",
                       cantidad AS "Cantidad",
                       precio_unitario AS "Precio Base Unit.",
                       descuento_aplicado AS "Item Disc. %", -- Asumiendo que esto es Item Disc
                       precio_total AS "Subtotal Costo"
                       -- Podrías añadir más columnas si las guardaste (ej. channel_deal_disc_costo)
                FROM detalle_productos
                WHERE cotizacion_id = {cotizacion_id_seleccionada} AND tipo_origen = 'costo'
            """, conn)
            st.dataframe(df_costo_detalle, use_container_width=True)

except sqlite3.Error as e:
    st.error(f"❌ Error de base de datos al cargar detalle: {e}")
except Exception as e:
     st.error(f"❌ Error inesperado al cargar detalle: {e}")
finally:
    if 'conn' in locals() and conn:
        conn.close()


# --- Generación de PDF ---

# Definición de la clase PDF (movida aquí para claridad)
class CotizacionPDFConLogo(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', logo_path="LOGO Syn Apps Sys_edited (2).png"):
        super().__init__(orientation, unit, format)
        self.logo_path = logo_path
        self.company_name = "SYNAPPSSYS" # Nombre de tu empresa
        self.alias_nb_pages() # Para tener numeración de páginas {nb}

    def header(self):
        try:
            if os.path.exists(self.logo_path):
                 self.image(self.logo_path, x=10, y=8, w=50)
            else:
                 self.set_font("Helvetica", "I", 8)
                 self.cell(50, 10, "(Logo no encontrado)")
        except Exception as e:
            print(f"Error cargando logo: {e}") # Log error si FPDF no puede cargar la imagen
            self.set_font("Helvetica", "I", 8)
            self.cell(50, 10, "(Error logo)")

        self.set_font("Helvetica", "B", 16)
        # Mover título a la derecha del logo
        self.set_xy(70, 15) # Ajustar coordenadas Y si es necesario
        self.cell(0, 10, "Propuesta Comercial", ln=False, align="L") # ln=False para que no salte línea

        # Línea divisoria debajo del header
        self.ln(15) # Espacio antes de la línea
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5) # Espacio después de la línea


    def footer(self):
        self.set_y(-15) # Posición a 1.5 cm del final
        self.set_font("Helvetica", "I", 8)
        # Línea divisoria arriba del footer
        self.set_line_width(0.2)
        self.line(10, self.get_y() - 2, 200, self.get_y() - 2)
        # Texto del footer
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}} | {self.company_name}", 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, title, ln=True, align="L")
        self.ln(2)

    def chapter_body(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, text)
        self.ln()

    def datos_cliente(self, datos):
        self.set_font("Helvetica", "B", 11)
        self.cell(95, 7, "Datos del Cliente", border='B', ln=True)
        # self.cell(95, 7, "Datos de la Propuesta", border='B', ln=True) # Mitad derecha
        self.ln(2)

        self.set_font("Helvetica", "", 10)
        col_width = 95 # Ancho para cada columna (aprox mitad de página A4 menos márgenes)
        y_start = self.get_y()

        # Columna Izquierda: Cliente/Contacto
        self.multi_cell(col_width, 6, f"Cliente: {datos.get('cliente', 'N/A')}\n"
                                    f"Contacto: {datos.get('contacto', 'N/A')}",
                                    border=0, align="L")
        y_left = self.get_y()
        self.set_y(y_start) # Volver al inicio Y

        # Columna Derecha: Propuesta/Fecha/Responsable
        self.set_x(10 + col_width + 5) # Mover a la derecha
        self.multi_cell(col_width, 6, f"Propuesta: {datos.get('propuesta', 'N/A')}\n"
                                     f"Fecha: {datos.get('fecha', 'N/A')}\n"
                                     f"Responsable: {datos.get('responsable', 'N/A')}",
                                     border=0, align="L")
        y_right = self.get_y()

        # Ajustar Y a la columna más larga
        self.set_y(max(y_left, y_right))
        self.ln(5)


    def tabla_productos(self, productos_venta_df):
        self.chapter_title("Detalle de Productos y Servicios")
        self.set_fill_color(220, 220, 220) # Gris claro para cabecera
        self.set_font("Helvetica", "B", 9)

        # Definir anchos de columnas (ajustar para que sumen ~190mm)
        w_prod = 75
        w_qty = 15
        w_unit = 25
        w_list = 25
        w_disc = 15
        w_total = 30
        h_cell = 7 # Altura de celda

        # Cabecera
        self.cell(w_prod, h_cell, "Producto / Servicio", 1, 0, "C", True)
        self.cell(w_qty, h_cell, "Cant.", 1, 0, "C", True)
        self.cell(w_unit, h_cell, "P. Unit. Lista", 1, 0, "C", True)
        self.cell(w_list, h_cell, "P. Total Lista", 1, 0, "C", True)
        self.cell(w_disc, h_cell, "Desc.%", 1, 0, "C", True)
        self.cell(w_total, h_cell, "Total", 1, 1, "C", True) # ln=1 (salto de línea)

        self.set_font("Helvetica", "", 9)
        fill = False # Para alternar colores de fila
        for index, row in productos_venta_df.iterrows():
            # Formatear números
            unit_price_str = f"${row['Precio Unit. Lista']:,.2f}"
            list_price_str = f"${row['Precio Total Lista']:,.2f}"
            discount_str = f"{row['Desc. %']:.1f}%"
            total_price_str = f"${row['Precio Final']:,.2f}"

            # MultiCell para productos largos (requiere calcular altura)
            # Simplificación: usar Cell, podría cortar nombres largos. Para manejo robusto, se necesitaría calcular altura.
            self.cell(w_prod, h_cell, str(row['Producto'])[:45], 1, 0, "L", fill) # Limitar longitud
            self.cell(w_qty, h_cell, str(row['Cantidad']), 1, 0, "C", fill)
            self.cell(w_unit, h_cell, unit_price_str, 1, 0, "R", fill)
            self.cell(w_list, h_cell, list_price_str, 1, 0, "R", fill)
            self.cell(w_disc, h_cell, discount_str, 1, 0, "R", fill)
            self.cell(w_total, h_cell, total_price_str, 1, 1, "R", fill)
            fill = not fill # Alternar color

        self.ln(5)

    def totales(self, total_venta):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Total Propuesta (USD): ${total_venta:,.2f}", border="T", ln=True, align="R")
        self.ln(5)

    def condiciones(self, vigencia, condiciones_texto):
        self.chapter_title("Condiciones Comerciales")
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, f"Vigencia de la propuesta: {vigencia}\n\n{condiciones_texto}")
        self.ln(5)

    def firma(self, responsable):
        self.ln(10) # Espacio antes de la firma
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, "Atentamente,", ln=True)
        self.ln(8) # Espacio para firma manuscrita
        self.cell(0, 6, responsable, ln=True)
        self.cell(0, 6, self.company_name, ln=True)


# Botón para generar PDF (solo si se ha seleccionado un detalle)
if cotizacion_id_seleccionada:
    st.divider()
    if st.button(f"📄 Generar PDF para Cliente (ID: {cotizacion_id_seleccionada})", key="generate_pdf"):
        try:
            # Re-conectar a la DB para obtener datos frescos para el PDF
            conn_pdf = conectar_db()
            datos_pdf_gen = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {cotizacion_id_seleccionada}", conn_pdf).iloc[0]
            df_venta_pdf = pd.read_sql_query(f"""
                SELECT producto AS "Producto",
                       cantidad AS "Cantidad",
                       precio_unitario AS "Precio Unit. Lista",
                       (precio_unitario * cantidad) AS "Precio Total Lista",
                       descuento_aplicado AS "Desc. %",
                       precio_total AS "Precio Final"
                FROM detalle_productos
                WHERE cotizacion_id = {cotizacion_id_seleccionada} AND tipo_origen = 'venta'
            """, conn_pdf)
            conn_pdf.close()

            # Crear instancia del PDF
            pdf = CotizacionPDFConLogo(logo_path="LOGO Syn Apps Sys_edited (2).png") # Asegúrate que la ruta al logo sea correcta
            pdf.add_page()

            # Llenar PDF
            pdf.datos_cliente(datos_pdf_gen)
            pdf.tabla_productos(df_venta_pdf)
            pdf.totales(datos_pdf_gen["total_venta"])
            pdf.condiciones(datos_pdf_gen["vigencia"], datos_pdf_gen["condiciones_comerciales"])
            pdf.firma(datos_pdf_gen["responsable"])

            # Guardar PDF temporalmente y ofrecer descarga
            pdf_output_filename = f"Cotizacion_{datos_pdf_gen['cliente']}_{datos_pdf_gen['propuesta']}_{cotizacion_id_seleccionada}.pdf".replace(" ", "_").replace("/", "-")
            pdf_output_path = os.path.join(APP_DIR, pdf_output_filename) # Guardar en el directorio de la app
            pdf.output(pdf_output_path)

            with open(pdf_output_path, "rb") as file:
                st.download_button(
                    label=f"📥 Descargar PDF: {pdf_output_filename}",
                    data=file,
                    file_name=pdf_output_filename, # Nombre que tendrá al descargar
                    mime="application/pdf"
                )
            # Opcional: eliminar el archivo PDF del servidor después de ofrecer la descarga
            # os.remove(pdf_output_path)

        except FileNotFoundError:
             st.error("❌ Error: No se encontró el archivo de logo para el PDF. Verifica la ruta 'LOGO Syn Apps Sys_edited (2).png'.")
        except sqlite3.Error as e:
            st.error(f"❌ Error de base de datos al generar PDF: {e}")
        except Exception as e:
            st.error(f"❌ Error inesperado al generar PDF: {e}")
            import traceback
            st.error(traceback.format_exc()) # Imprime más detalles del error
