
import streamlit as st
import sqlite3
import pandas as pd

DB_PATH = "crm_cotizaciones.sqlite"

def conectar_db():
    return sqlite3.connect(DB_PATH)

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
