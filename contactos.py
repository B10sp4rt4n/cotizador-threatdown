# contactos.py
import streamlit as st
import pandas as pd
from database import conectar_db
from empresas import mostrar_empresas

def agregar_contacto(datos):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO contactos (
            nombre, apellido_paterno, apellido_materno, correo, telefono, empresa_id
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datos["nombre"], datos["apellido_paterno"], datos["apellido_materno"],
        datos["correo"], datos["telefono"], datos["empresa_id"]
    ))
    conn.commit()
    conn.close()

def mostrar_contactos():
    conn = conectar_db()
    df = pd.read_sql_query("""
        SELECT c.*, e.razon_social AS empresa 
        FROM contactos c
        LEFT JOIN empresas e ON c.empresa_id = e.id
        ORDER BY e.razon_social, c.nombre
    """, conn)
    conn.close()
    return df

def vista_contactos():
    st.title("👥 Gestión de Contactos")

    with st.expander("➕ Agregar nuevo contacto"):
        empresas = mostrar_empresas()
        if empresas.empty:
            st.warning("⚠️ Primero debes registrar al menos una empresa.")
            st.stop()

        with st.form("form_nuevo_contacto"):
            nombre = st.text_input("Nombre")
            apellido_paterno = st.text_input("Apellido Paterno")
            apellido_materno = st.text_input("Apellido Materno")
            correo = st.text_input("Correo electrónico")
            telefono = st.text_input("Teléfono")
            empresa_nombre = st.selectbox("Empresa asociada", empresas["razon_social"].tolist())
            empresa_id = empresas[empresas["razon_social"] == empresa_nombre].iloc[0]["id"]

            submitted = st.form_submit_button("Guardar contacto")
            if submitted:
                datos = {
                    "nombre": nombre,
                    "apellido_paterno": apellido_paterno,
                    "apellido_materno": apellido_materno,
                    "correo": correo,
                    "telefono": telefono,
                    "empresa_id": empresa_id
                }
                agregar_contacto(datos)
                st.success("✅ Contacto guardado exitosamente")

    st.subheader("📋 Lista de Contactos")
    df = mostrar_contactos()
    st.dataframe(df, use_container_width=True)
