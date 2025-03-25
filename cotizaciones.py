# cotizaciones.py
import sqlite3
import pandas as pd
from database import conectar_db

def guardar_cotizacion(datos, productos_venta, productos_costo):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cotizaciones (
            cliente, contacto, propuesta, fecha, responsable,
            total_venta, total_costo, utilidad, margen,
            vigencia, condiciones_comerciales, usuario_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datos["cliente"], datos["contacto"], datos["propuesta"], datos["fecha"], datos["responsable"],
        datos["total_venta"], datos["total_costo"], datos["utilidad"], datos["margen"],
        datos["vigencia"], datos["condiciones_comerciales"], datos["usuario_id"]
    ))
    cotizacion_id = cursor.lastrowid

    for p in productos_venta:
        cursor.execute("""
            INSERT INTO detalle_productos (
                cotizacion_id, producto, cantidad, precio_unitario,
                precio_total, descuento_aplicado, tipo_origen
            ) VALUES (?, ?, ?, ?, ?, ?, 'venta')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Unitario de Lista"],
            p["Precio Total con Descuento"], p["Descuento %"]
        ))

    for p in productos_costo:
        cursor.execute("""
            INSERT INTO detalle_productos (
                cotizacion_id, producto, cantidad, precio_unitario,
                precio_total, descuento_aplicado, tipo_origen
            ) VALUES (?, ?, ?, ?, ?, ?, 'costo')
        """, (
            cotizacion_id, p["Producto"], p["Cantidad"], p["Precio Base"],
            p["Subtotal"], p["Item Disc. %"]
        ))

    conn.commit()
    conn.close()
    return cotizacion_id

def ver_historial(usuario):
    conn = conectar_db()
    if usuario["tipo"] == "superadmin":
        query = "SELECT * FROM cotizaciones ORDER BY fecha DESC"
    elif usuario["tipo"] == "admin":
        query = f"""
            SELECT * FROM cotizaciones
            WHERE usuario_id IN (
                SELECT id FROM usuarios WHERE admin_id = {usuario['id']} OR id = {usuario['id']}
            ) ORDER BY fecha DESC
        """
    else:
        query = f"SELECT * FROM cotizaciones WHERE usuario_id = {usuario['id']} ORDER BY fecha DESC"

    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def obtener_detalle_cotizacion(cotizacion_id):
    conn = conectar_db()
    datos = pd.read_sql_query(f"SELECT * FROM cotizaciones WHERE id = {cotizacion_id}", conn).iloc[0]

    venta = pd.read_sql_query(f"""
        SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
        FROM detalle_productos
        WHERE cotizacion_id = {cotizacion_id} AND tipo_origen = 'venta'
    """, conn)

    costo = pd.read_sql_query(f"""
        SELECT producto, cantidad, precio_unitario, precio_total, descuento_aplicado
        FROM detalle_productos
        WHERE cotizacion_id = {cotizacion_id} AND tipo_origen = 'costo'
    """, conn)

    conn.close()
    return datos, venta, costo
