# app.py
import streamlit as st
from datetime import date
import pandas as pd
from database import inicializar_db
from auth import autenticar_usuario, crear_usuario, actualizar_contrasena
from clientes import vista_clientes, mostrar_clientes
from cotizaciones import guardar_cotizacion, ver_historial, obtener_detalle_cotizacion
from pdf_utils import CotizacionPDFConLogo

inicializar_db()

# desde aqui el agregado

from auth import hash_password  # asegúrate de que esté importado

# Verificar si hay usuarios
import sqlite3
from database import conectar_db

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
            if contrasena != confirmar:
                st.error("❌ Las contraseñas no coinciden.")
            else:
                crear_usuario(nombre, correo, contrasena, "superadmin", None)
                st.success("✅ Usuario creado. Reinicia la app e inicia sesión.")
    st.stop()

# hasta aqui los cambios


if "usuario" not in st.session_state:
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
    else:
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

st.markdown(f"## 👋 Bienvenido, **{st.session_state.usuario['nombre']}** ({st.session_state.usuario['tipo']})")

menu = st.sidebar.selectbox("Secciones", ["Cotizaciones", "Clientes"])
if menu == "Clientes":
    vista_clientes()
    st.stop()

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

st.write("⬇️ Aquí iría la lógica de productos y precios (cargar Excel, calcular descuentos, etc.)")

# Simulación de resumen para demostración
precio_venta_total = 10000
costo_total = 7000
utilidad = precio_venta_total - costo_total
margen = (utilidad / precio_venta_total) * 100

st.subheader("Resumen")
st.metric("Total Venta", f"${precio_venta_total:,.2f}")
st.metric("Total Costo", f"${costo_total:,.2f}")
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
    dummy_productos = [{"Producto": "Servicio X", "Cantidad": 1, "Precio Unitario de Lista": 10000, "Precio Total con Descuento": 10000, "Descuento %": 0}]
    dummy_costos = [{"Producto": "Base X", "Cantidad": 1, "Precio Base": 7000, "Subtotal": 7000, "Item Disc. %": 0}]
    cot_id = guardar_cotizacion(datos, dummy_productos, dummy_costos)
    st.success(f"✅ Cotización #{cot_id} guardada")

st.subheader("📋 Historial")
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
