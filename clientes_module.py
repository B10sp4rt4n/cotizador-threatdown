import streamlit as st
import pandas as pd
import sqlite3

DB_PATH = "crm_cotizaciones.sqlite"

def conectar_db():
    return sqlite3.connect(DB_PATH)

def crear_tabla_clientes():
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

def agregar_cliente(datos):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (
                nombre, apellido_paterno, apellido_materno, empresa, correo, telefono,
                rfc, calle, numero_exterior, numero_interior, codigo_postal,
                municipio, ciudad, estado, notas
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos["nombre"], datos["apellido_paterno"], datos["apellido_materno"], datos["empresa"],
            datos["correo"], datos["telefono"], datos["rfc"], datos["calle"], datos["numero_exterior"],
            datos["numero_interior"], datos["codigo_postal"], datos["municipio"], datos["ciudad"],
            datos["estado"], datos["notas"]
        ))
        conn.commit()
    except Exception as e:
        st.error(f"Error al insertar cliente: {e}")
    finally:
        conn.close()

def mostrar_clientes():
    conn = conectar_db()
    try:
        df = pd.read_sql_query("SELECT * FROM clientes ORDER BY empresa ASC", conn)
        return df
    except Exception as e:
        st.error(f"Error al consultar clientes: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def vista_clientes():
    crear_tabla_clientes()
    st.header("Gestión de Clientes")

    with st.form("form_cliente"):
        nombre = st.text_input("Nombre")
        apellido_paterno = st.text_input("Apellido Paterno")
        apellido_materno = st.text_input("Apellido Materno")
        empresa = st.text_input("Empresa")
        correo = st.text_input("Correo Electrónico")
        telefono = st.text_input("Teléfono")
        rfc = st.text_input("RFC")
        calle = st.text_input("Calle")
        numero_exterior = st.text_input("Número Exterior")
        numero_interior = st.text_input("Número Interior")
        codigo_postal = st.text_input("Código Postal")
        municipio = st.text_input("Municipio")
        ciudad = st.text_input("Ciudad")
        estado = st.text_input("Estado")
        notas = st.text_area("Notas")

        submitted = st.form_submit_button("Guardar Cliente")
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
            st.success("Cliente guardado correctamente")

    st.subheader("Lista de Clientes")
    df = mostrar_clientes()
    st.dataframe(df)
