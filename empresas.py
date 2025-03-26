# empresas.py
import streamlit as st
import pandas as pd
from database import conectar_db

def agregar_empresa(datos):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO empresas (
            razon_social, rfc, calle, numero_exterior, numero_interior,
            codigo_postal, municipio, ciudad, estado, notas
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["razon_social"], datos["rfc"], datos["calle"], datos["numero_exterior"],
        datos["numero_interior"], datos["codigo_postal"], datos["municipio"],
        datos["ciudad"], datos["estado"], datos["notas"]
    ))
    conn.commit()
    conn.close()

def mostrar_empresas():
    conn = conectar_db()
    df = pd.read_sql_query("SELECT * FROM empresas ORDER BY razon_social ASC", conn)
    conn.close()
    return df

def vista_empresas():
    st.title("🏢 Gestión de Empresas")

    with st.expander("➕ Agregar nueva empresa"):
        with st.form("form_nueva_empresa"):
            razon_social = st.text_input("Razón Social")
            rfc = st.text_input("RFC")
            calle = st.text_input("Calle")
            numero_exterior = st.text_input("Número Exterior")
            numero_interior = st.text_input("Número Interior")
            codigo_postal = st.text_input("Código Postal")
            municipio = st.text_input("Municipio")
            ciudad = st.text_input("Ciudad")
            estado = st.text_input("Estado")
            notas = st.text_area("Notas")

            submitted = st.form_submit_button("Guardar empresa")
            if submitted:
                datos = {
                    "razon_social": razon_social,
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
                agregar_empresa(datos)
                st.success("✅ Empresa guardada exitosamente")

    st.subheader("📋 Lista de Empresas")
    df = mostrar_empresas()
    st.dataframe(df, use_container_width=True)
