import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import date
from fpdf import FPDF

# ========================
# Configuración inicial
# ========================
DB_PATH = os.path.join(os.getcwd(), "crm_cotizaciones.sqlite")
LOGO_PATH = "LOGO Syn Apps Sys_edited (2).png"

# ========================
# Funciones de base de datos
# ========================
def inicializar_db():
    """Crea la estructura inicial de la base de datos"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, contacto TEXT, propuesta TEXT,
                fecha TEXT, responsable TEXT, total_venta REAL,
                total_costo REAL, utilidad REAL, margen REAL,
                vigencia TEXT, condiciones_comerciales TEXT
            )""")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER, producto TEXT, cantidad INTEGER,
                precio_unitario REAL, precio_total REAL,
                descuento_aplicado REAL, tipo_origen TEXT,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
            )""")

        # Verificar y agregar columnas nuevas
        columnas = [col[1] for col in cursor.execute("PRAGMA table_info(cotizaciones)").fetchall()]
        for columna in ['vigencia', 'condiciones_comerciales']:
            if columna not in columnas:
                cursor.execute(f"ALTER TABLE cotizaciones ADD COLUMN {columna} TEXT;")

def conectar_db():
    return sqlite3.connect(DB_PATH)

# ========================
# Funciones de carga de datos
# ========================
@st.cache_data
def cargar_datos():
    """Carga y prepara los datos desde el archivo Excel"""
    try:
        df = pd.read_excel("precios_threatdown.xlsx")
        df["Tier Min"] = pd.to_numeric(df["Tier Min"], errors="coerce")
        df["Tier Max"] = pd.to_numeric(df["Tier Max"], errors="coerce")
        return df.dropna(subset=["Tier Min", "Tier Max"])
    except FileNotFoundError:
        st.error("❌ Archivo 'precios_threatdown.xlsx' no encontrado")
        st.stop()
    except Exception as e:
        st.error(f"Error cargando datos: {str(e)}")
        st.stop()

# ========================
# Componentes reutilizables
# ========================
def mostrar_encabezado():
    st.title("Cotizador ThreatDown con CRM")
    with st.sidebar:
        st.header("Datos de la cotización")
        return {
            "cliente": st.text_input("Cliente"),
            "contacto": st.text_input("Nombre de contacto"),
            "propuesta": st.text_input("Nombre de la propuesta"),
            "fecha": st.date_input("Fecha", value=date.today()),
            "responsable": st.text_input("Responsable / Vendedor")
        }

def mostrar_condiciones():
    col1, col2 = st.columns(2)
    with col1:
        vigencia = st.text_input("Vigencia de la propuesta", value="30 días")
    with col2:
        condiciones = st.text_area(
            "Condiciones Comerciales",
            value="Precios en USD. Pago contra entrega. No incluye impuestos.",
            height=100
        )
    return vigencia, condiciones

# ========================
# Lógica principal
# ========================
def main():
    inicializar_db()
    datos_cliente = mostrar_encabezado()
    vigencia, condiciones = mostrar_condiciones()
    
    # Carga de precios
    df_precios = cargar_datos()
    
    # Selección de productos
    termino = st.selectbox(
        "Plazo del servicio (meses):",
        options=sorted(df_precios["Term (Month)"].dropna().unique())
    )
    
    df_filtrado = df_precios[df_precios["Term (Month)"] == termino]
    productos_seleccionados = st.multiselect(
        "Productos a cotizar:",
        df_filtrado["Product Title"].unique()
    )
    
    # Procesamiento de productos
    costos = []
    ventas = []
    
    for prod in productos_seleccionados:
        df_producto = df_filtrado[df_filtrado["Product Title"] == prod]
        cantidad = st.number_input(f"Cantidad de '{prod}':", min_value=1, value=1)
        
        # Validar rango de cantidad
        rango_valido = df_producto[
            (df_producto["Tier Min"] <= cantidad) & 
            (df_producto["Tier Max"] >= cantidad)
        ]
        
        if rango_valido.empty:
            st.warning(f"Rango no válido para {prod} con cantidad {cantidad}")
            continue
            
        precio_base = rango_valido.iloc[0]["MSRP USD"]
        
        # Inputs de descuentos
        cols = st.columns(3)
        with cols[0]: item_disc = st.number_input(f"Item Disc (%) - {prod}", 0.0, 100.0, 0.0)
        with cols[1]: channel_disc = st.number_input(f"Channel Disc (%) - {prod}", 0.0, 100.0, 0.0)
        with cols[2]: deal_disc = st.number_input(f"Deal Reg Disc (%) - {prod}", 0.0, 100.0, 0.0)
        total_descuento = item_disc + channel_disc + deal_disc
        
        # Nuevos cálculos con descuento total
        precio_total_lista = precio_base * cantidad
        monto_descuento = precio_total_lista * (total_descuento / 100)
        precio_final = precio_total_lista - monto_descuento
        
        costos.append({
            "Producto": prod, "Cantidad": cantidad, 
            "Precio Base": precio_base, "Item Disc. %": item_disc,
            "Subtotal": round(precio_final, 2)
        })
        
        ventas.append({
            "Producto": prod,
            "Cantidad": cantidad,
            "Precio Unitario Lista": round(precio_base, 2),
            "Precio Total Lista": round(precio_total_lista, 2),
            "Descuento %": total_descuento,
            "Monto Descuento": round(monto_descuento, 2),
            "Precio Total con Descuento": round(precio_final, 2)
        })
    
    # Mostrar resultados
    if costos and ventas:
        df_costos = pd.DataFrame(costos)
        df_ventas = pd.DataFrame(ventas)
        
        st.subheader("📊 Resumen de Costos")
        st.dataframe(df_costos.style.format({
            'Precio Base': '${:.2f}',
            'Subtotal': '${:.2f}'
        }))
        
        st.subheader("📈 Resumen de Ventas")
        column_order = [
            'Producto', 'Cantidad', 'Precio Unitario Lista', 
            'Precio Total Lista', 'Descuento %', 'Monto Descuento', 
            'Precio Total con Descuento'
        ]
        st.dataframe(df_ventas[column_order].style.format({
            'Precio Unitario Lista': '${:,.2f}',
            'Precio Total Lista': '${:,.2f}',
            'Descuento %': '{:.2f}%',
            'Monto Descuento': '${:,.2f}',
            'Precio Total con Descuento': '${:,.2f}'
        }))
        
        # Cálculo de utilidad
        total_venta = df_ventas["Precio Total con Descuento"].sum()
        total_costo = df_costos["Subtotal"].sum()
        utilidad = total_venta - total_costo
        margen = (utilidad / total_venta) * 100 if total_venta > 0 else 0
        
        st.subheader("💰 Rentabilidad")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Venta", f"${total_venta:,.2f}")
        col2.metric("Total Costo", f"${total_costo:,.2f}")
        col3.metric("Utilidad Neta", f"${utilidad:,.2f}")
        st.metric("**Margen de Ganancia**", f"{margen:.2f}%")
        
        # Guardar en base de datos
        if st.button("💾 Guardar Cotización"):
            datos = {
                **datos_cliente,
                "total_venta": total_venta,
                "total_costo": total_costo,
                "utilidad": utilidad,
                "margen": margen,
                "vigencia": vigencia,
                "condiciones_comerciales": condiciones
            }
            
            with conectar_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO cotizaciones (
                        cliente, contacto, propuesta, fecha, responsable,
                        total_venta, total_costo, utilidad, margen,
                        vigencia, condiciones_comerciales
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    tuple(datos.values()))
                
                cotizacion_id = cursor.lastrowid
                
                # Insertar detalles de venta
                for producto in df_ventas.to_dict("records"):
                    cursor.execute("""
                        INSERT INTO detalle_productos (
                            cotizacion_id, producto, cantidad, precio_unitario,
                            precio_total, descuento_aplicado, tipo_origen
                        ) VALUES (?,?,?,?,?,?,?)""",
                        (cotizacion_id, producto["Producto"], producto["Cantidad"],
                         producto["Precio Unitario Lista"],
                         producto["Precio Total con Descuento"],
                         producto["Descuento %"], 'venta'))
                
                # Insertar detalles de costo
                for producto in df_costos.to_dict("records"):
                    cursor.execute("""
                        INSERT INTO detalle_productos (
                            cotizacion_id, producto, cantidad, precio_unitario,
                            precio_total, descuento_aplicado, tipo_origen
                        ) VALUES (?,?,?,?,?,?,?)""",
                        (cotizacion_id, producto["Producto"], producto["Cantidad"],
                         producto["Precio Base"],
                         producto["Subtotal"],
                         producto["Item Disc. %"], 'costo'))
                
                conn.commit()
                st.success("✅ Cotización guardada exitosamente!")

if __name__ == "__main__":
    main()
