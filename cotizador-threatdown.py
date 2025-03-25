# app.py (versión completa con autenticación y lógica del cotizador)
import streamlit as st
from datetime import date
import pandas as pd
from database import inicializar_db, conectar_db
from auth import autenticar_usuario, crear_usuario, actualizar_contrasena
from clientes import vista_clientes, mostrar_clientes
from cotizaciones import guardar_cotizacion, ver_historial, obtener_detalle_cotizacion
from pdf_utils import CotizacionPDFConLogo
import os

inicializar_db()

# Verificar si hay usuarios existentes y registrar superadmin si es la primera vez
conn = conectar_db()
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM usuarios")
usuario_count = cursor.fetchone()[0]
conn.close()

if "usuario" not in st.session_state:
    if usuario_count == 0:
        st.title("🆕 Registro inicial de Superadministrador")
        with st.form("registro_inicial"):
            nombre = st.text_input("Nombre completo")
            correo = st.text_input("Correo")
            contrasena = st.text_input("Contraseña", type="password")
            confirmar = st.text_input("Confirmar contraseña", type="password")
            submitted = st.form_submit_button("Crear Superadmin")
            if submitted:
                if contrasena != confirmar:
                    st.error("❌ Las contraseñas no coinciden.")
                else:
                    crear_usuario(nombre, correo, contrasena, "superadmin", None)
                    st.success("✅ Usuario creado. Reinicia la app e inicia sesión.")
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
                        actualizar_contrasena(correo_reset, nueva)
                        st.success("✅ Contraseña actualizada. Ahora puedes iniciar sesión.")
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

# ============ Interfaz autenticada ============

st.markdown(f"## 👋 Bienvenido, **{st.session_state.usuario['nombre']}** ({st.session_state.usuario['tipo']})")
st.markdown(f"📅 Fecha actual: **{date.today().strftime('%Y-%m-%d')}**")

menu = st.sidebar.selectbox("Secciones", ["Cotizaciones", "Clientes"])
if menu == "Clientes":
    vista_clientes()
    st.stop()

# ======================= Carga de datos de Excel =======================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("precios_threatdown.xlsx")
    df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
    df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
    return df.dropna(subset=["Tier Min", "Tier Max"])

df_precios = cargar_datos()

# ======================= Datos del cliente =======================
st.sidebar.header("Datos de la cotización")
df_clientes = mostrar_clientes()
if df_clientes.empty:
    st.sidebar.warning("⚠️ No hay clientes registrados. Agrega uno en la sección 'Clientes'.")
    st.stop()

empresa_seleccionada = st.sidebar.selectbox("Selecciona la empresa cliente", df_clientes["empresa"].unique())
cliente_row = df_clientes[df_clientes["empresa"] == empresa_seleccionada].iloc[0]
cliente = empresa_seleccionada
contacto = cliente_row["nombre"] + " " + cliente_row["apellido_paterno"] + " " + cliente_row["apellido_materno"]

propuesta = st.sidebar.text_input("Nombre de la propuesta")
fecha = st.sidebar.date_input("Fecha", value=date.today())
responsable = st.sidebar.text_input("Responsable / Vendedor")
vigencia = st.text_input("Vigencia de la propuesta", value="30 días")
condiciones_comerciales = st.text_area("Condiciones comerciales", value="Precios en USD. Pago contra entrega. No incluye impuestos.", height=100)

terminos_disponibles = sorted(df_precios["Term (Month)"].dropna().unique())
termino_seleccionado = st.selectbox("Selecciona el plazo del servicio (en meses):", terminos_disponibles)

# ======================= Selección de productos =======================
df_filtrado = df_precios[df_precios["Term (Month)"] == termino_seleccionado]
productos = df_filtrado["Product Title"].unique()
seleccion = st.multiselect("Selecciona productos a cotizar:", productos)

cotizacion = []
productos_para_tabla_secundaria = []

for prod in seleccion:
    df_producto = df_filtrado[df_filtrado["Product Title"] == prod]
    cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1, step=1)
    df_rango = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]

    if not df_rango.empty:
        fila = df_rango.iloc[0]
        precio_base = fila["MSRP USD"]

        item_disc = st.number_input(f"Descuento 'Item' (%) para '{prod}':", 0.0, 100.0, 0.0)
        channel_disc = st.number_input(f"Channel Disc. (%) para '{prod}':", 0.0, 100.0, 0.0)
        deal_reg_disc = st.number_input(f"Deal Reg. Disc. (%) para '{prod}':", 0.0, 100.0, 0.0)

        precio1 = precio_base * (1 - item_disc / 100)
        precio_final = precio1 * (1 - (channel_disc + deal_reg_disc) / 100)
        subtotal = precio_final * cantidad

        cotizacion.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Base": precio_base,
            "Item Disc. %": item_disc,
            "Channel + Deal Disc. %": channel_disc + deal_reg_disc,
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

# ======================= Tabla resumen =======================
costo_total = sum(p["Subtotal"] for p in cotizacion) if cotizacion else 0

precio_venta_total = 0
venta_tabla = []
for item in productos_para_tabla_secundaria:
    cantidad = item["Cantidad"]
    precio_unitario = item["Precio Unitario de Lista"]
    precio_total_lista = cantidad * precio_unitario

    descuento_directo = st.number_input(f"Descuento directo (%) sobre lista para '{item['Producto']}':", 0.0, 100.0, 0.0, key=f"desc_{item['Producto']}")
    precio_con_descuento = precio_total_lista * (1 - descuento_directo / 100)

    venta_tabla.append({
        "Producto": item["Producto"],
        "Cantidad": cantidad,
        "Precio Unitario de Lista": round(precio_unitario, 2),
        "Precio Total de Lista": round(precio_total_lista, 2),
        "Descuento %": descuento_directo,
        "Precio Total con Descuento": round(precio_con_descuento, 2)
    })

precio_venta_total = sum(p["Precio Total con Descuento"] for p in venta_tabla)

if precio_venta_total and costo_total:
    utilidad = precio_venta_total - costo_total
    margen = (utilidad / precio_venta_total) * 100

    st.subheader("Resumen financiero")
    st.metric("Venta total", f"${precio_venta_total:,.2f}")
    st.metric("Costo total", f"${costo_total:,.2f}")
    st.metric("Utilidad", f"${utilidad:,.2f}")
    st.metric("Margen", f"{margen:.2f}%")

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
            "condiciones_comerciales": condiciones_comerciales,
            "usuario_id": st.session_state.usuario["id"]
        }
        guardar_cotizacion(datos, venta_tabla, cotizacion)
        st.success("✅ Cotización guardada en CRM")

# ======================= Historial y PDF =======================
st.subheader("📋 Historial de cotizaciones")
df_hist = ver_historial(st.session_state.usuario)
st.dataframe(df_hist)

st.subheader("🔍 Detalle de cotización")
if not df_hist.empty:
    df_hist["Resumen"] = df_hist["fecha"] + " - " + df_hist["cliente"] + " - " + df_hist["propuesta"]
    seleccion = st.selectbox("Selecciona una cotización", df_hist["Resumen"])
    if seleccion:
        cot_id = int(df_hist[df_hist["Resumen"] == seleccion]["id"].values[0])
        datos, df_venta, df_costo = obtener_detalle_cotizacion(cot_id)

        st.markdown(f"**Cliente:** {datos['cliente']}")
        st.markdown(f"**Contacto:** {datos['contacto']}")
        st.markdown(f"**Propuesta:** {datos['propuesta']}")
        st.markdown(f"**Total Venta:** ${datos['total_venta']:,.2f}")

        if st.button("📄 Generar PDF"):
            pdf = CotizacionPDFConLogo()
            pdf.add_page()
            pdf.encabezado_cliente(datos)
            pdf.tabla_productos(df_venta.to_dict("records"))
            pdf.totales(datos["total_venta"])
            pdf.condiciones(datos["vigencia"], datos["condiciones_comerciales"])
            pdf.firma(datos["responsable"])
            path = f"cotizacion_cliente_{cot_id}.pdf"
            pdf.output(path)
            with open(path, "rb") as f:
                st.download_button("📥 Descargar PDF", f, file_name=path, mime="application/pdf")
