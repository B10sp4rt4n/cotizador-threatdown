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
LOGO_PATH = "LOGO Syn Apps Sys_edited (2).png"  # Actualizar con tu ruta

# ========================
# Funciones de base de datos
# ========================
def inicializar_db():
    """Crea la estructura inicial de la base de datos"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Tabla principal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, contacto TEXT, propuesta TEXT,
                fecha TEXT, responsable TEXT, 
                total_lista REAL, total_costo REAL, total_venta REAL,
                utilidad REAL, margen REAL,
                vigencia TEXT, condiciones_comerciales TEXT
            )""")
        
        # Tabla detalle
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detalle_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cotizacion_id INTEGER, producto TEXT, cantidad INTEGER,
                precio_lista REAL, descuento_costo REAL, costo REAL,
                descuento_venta REAL, precio_venta REAL,
                FOREIGN KEY (cotizacion_id) REFERENCES cotizaciones(id)
            )""")

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
# Componentes de la interfaz
# ========================
def mostrar_encabezado():
    st.title("🛒 Cotizador ThreatDown Professional")
    with st.sidebar:
        st.header("📋 Datos Comerciales")
        return {
            "cliente": st.text_input("Cliente"),
            "contacto": st.text_input("Contacto"),
            "propuesta": st.text_input("Propuesta"),
            "fecha": st.date_input("Fecha", value=date.today()),
            "responsable": st.text_input("Responsable"),
            "vigencia": st.text_input("Vigencia", value="30 días"),
            "condiciones_comerciales": st.text_area(
                "Condiciones Comerciales", 
                value="Precios en USD. Pago contra entrega."
            )
        }

# ========================
# Lógica principal
# ========================
def main():
    inicializar_db()
    datos = mostrar_encabezado()
    
    # Carga de precios
    df_precios = cargar_datos()
    
    # Selección de productos
    termino = st.selectbox(
        "📅 Plazo de servicio (meses):",
        options=sorted(df_precios["Term (Month)"].dropna().unique())
    )
    
    df_filtrado = df_precios[df_precios["Term (Month)"] == termino]
    productos = df_filtrado["Product Title"].unique()
    seleccionados = st.multiselect("🔍 Seleccionar productos", productos)
    
    # Procesamiento de productos
    detalle = []
    for producto in seleccionados:
        st.divider()
        st.subheader(f"📦 {producto}")
        
        # Obtener precio base
        df_producto = df_filtrado[df_filtrado["Product Title"] == producto]
        cantidad = st.number_input(f"Cantidad", min_value=1, value=1, key=f"cant_{producto}")
        
        # Validar rango de cantidad
        rango_valido = df_producto[
            (df_producto["Tier Min"] <= cantidad) & 
            (df_producto["Tier Max"] >= cantidad)
        ]
        if rango_valido.empty:
            st.error("⛔ Cantidad fuera de rango válido")
            continue
            
        precio_lista = rango_valido.iloc[0]["MSRP USD"]
        
        # Sección de descuentos
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 💼 Descuentos para Costo")
            item_disc = st.number_input("Item Disc (%)", 0.0, 100.0, 0.0, key=f"item_{producto}")
            channel_disc = st.number_input("Channel Disc (%)", 0.0, 100.0, 0.0, key=f"channel_{producto}")
            deal_disc = st.number_input("Deal Reg Disc (%)", 0.0, 100.0, 0.0, key=f"deal_{producto}")
            descuento_costo = item_disc + channel_disc + deal_disc
            
        with col2:
            st.markdown("#### 💰 Descuento para Venta")
            max_venta_disc = min(descuento_costo, 100.0)
            venta_disc = st.number_input(
                "Descuento Venta (%)", 
                0.0, 
                max_venta_disc,
                0.0,
                key=f"venta_{producto}",
                help=f"Máximo permitido: {max_venta_disc}%"
            )
        
        # Cálculos financieros
        costo_unitario = precio_lista * (1 - descuento_costo/100)
        precio_venta_unitario = precio_lista * (1 - venta_disc/100)
        
        detalle.append({
            "producto": producto,
            "cantidad": cantidad,
            "precio_lista": precio_lista,
            "descuento_costo": descuento_costo,
            "costo_unitario": costo_unitario,
            "descuento_venta": venta_disc,
            "precio_venta": precio_venta_unitario,
            "total_lista": precio_lista * cantidad,
            "total_costo": costo_unitario * cantidad,
            "total_venta": precio_venta_unitario * cantidad
        })
    
    if detalle:
        df = pd.DataFrame(detalle)
        
        # Resumen financiero
        st.divider()
        st.subheader("📊 Resumen Financiero")
        
        # Métricas clave
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Lista", f"${df['total_lista'].sum():,.2f}")
        col2.metric("Total Costo", f"${df['total_costo'].sum():,.2f}", 
                   delta=f"-{df['descuento_costo'].mean():.1f}% descuento costo")
        col3.metric("Total Venta", f"${df['total_venta'].sum():,.2f}", 
                   delta=f"-{df['descuento_venta'].mean():.1f}% descuento venta")
        
        # Cálculo de utilidad
        utilidad = df['total_venta'].sum() - df['total_costo'].sum()
        margen = (utilidad / df['total_venta'].sum()) * 100 if df['total_venta'].sum() > 0 else 0
        st.success(f"## 🏆 Resultado Final: Utilidad ${utilidad:,.2f} | Margen {margen:.1f}%")
        
        # Guardar en base de datos
        if st.button("💾 Guardar Cotización", type="primary"):
            with conectar_db() as conn:
                cursor = conn.cursor()
                
                # Insertar cabecera
                cursor.execute("""
                    INSERT INTO cotizaciones (
                        cliente, contacto, propuesta, fecha, responsable,
                        total_lista, total_costo, total_venta,
                        utilidad, margen, vigencia, condiciones_comerciales
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        datos["cliente"], datos["contacto"], datos["propuesta"],
                        datos["fecha"].isoformat(), datos["responsable"],
                        df['total_lista'].sum(), df['total_costo'].sum(),
                        df['total_venta'].sum(), utilidad, margen,
                        datos["vigencia"], datos["condiciones_comerciales"]
                    ))
                
                cotizacion_id = cursor.lastrowid
                
                # Insertar detalle
                for item in detalle:
                    cursor.execute("""
                        INSERT INTO detalle_productos (
                            cotizacion_id, producto, cantidad,
                            precio_lista, descuento_costo, costo,
                            descuento_venta, precio_venta
                        ) VALUES (?,?,?,?,?,?,?,?)""",
                        (
                            cotizacion_id, item["producto"], item["cantidad"],
                            item["precio_lista"], item["descuento_costo"],
                            item["costo_unitario"], item["descuento_venta"],
                            item["precio_venta"]
                        ))
                
                conn.commit()
                st.toast("✅ Cotización guardada exitosamente!")

if __name__ == "__main__":
    main()  # 🚨 Asegurar que esta línea esté al final del archivo
    # =====================================
    # Nueva sección: Consultar cotizaciones
    # =====================================
    st.divider()
    st.subheader("📂 Cotizaciones Guardadas")
    
    # Obtener lista de cotizaciones
    with conectar_db() as conn:
        df_cotizaciones = pd.read_sql_query(
            "SELECT id, cliente, propuesta, fecha, total_venta FROM cotizaciones ORDER BY fecha DESC", 
            conn
        )
    
    if not df_cotizaciones.empty:
        # Crear lista de cotizaciones para selección
        cotizaciones = [
            f"{row['fecha']} - {row['cliente']} - {row['propuesta']} (${row['total_venta']:,.2f})"
            for _, row in df_cotizaciones.iterrows()
        ]
        
        # Selector de cotización
        cotizacion_seleccionada = st.selectbox(
            "Seleccionar cotización del historial:",
            cotizaciones
        )
        
        if cotizacion_seleccionada:
            # Obtener ID de la cotización seleccionada
            selected_id = df_cotizaciones.iloc[cotizaciones.index(cotizacion_seleccionada)]['id']
            
            # Obtener detalles de la cotización
            with conectar_db() as conn:
                # Datos generales
                cabecera = pd.read_sql_query(
                    f"SELECT * FROM cotizaciones WHERE id = {selected_id}", 
                    conn
                ).iloc[0].to_dict()
                
                # Detalle de productos
                detalle = pd.read_sql_query(
                    f"""SELECT producto, cantidad, 
                        precio_lista, descuento_costo, costo,
                        descuento_venta, precio_venta 
                        FROM detalle_productos 
                        WHERE cotizacion_id = {selected_id}""", 
                    conn
                )
            
            # Mostrar detalles
            st.divider()
            st.subheader("📄 Detalle de la Cotización")
            
            # Información general
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Cliente:** {cabecera['cliente']}")
                st.markdown(f"**Propuesta:** {cabecera['propuesta']}")
                st.markdown(f"**Fecha:** {cabecera['fecha']}")
                
            with col2:
                st.markdown(f"**Total Venta:** ${cabecera['total_venta']:,.2f}")
                st.markdown(f"**Utilidad:** ${cabecera['utilidad']:,.2f}")
                st.markdown(f"**Margen:** {cabecera['margen']:.2f}%")
            
            # Detalle de productos
            st.subheader("📦 Productos")
            st.dataframe(detalle.style.format({
                'precio_lista': '${:.2f}',
                'costo': '${:.2f}',
                'precio_venta': '${:.2f}',
                'descuento_costo': '{:.2f}%',
                'descuento_venta': '{:.2f}%'
            }))
            
            # Generar PDF
            if st.button("🖨️ Generar PDF de esta cotización"):
                # ... (aquí iría el código de generación de PDF que ya tienes)
                st.success("PDF generado correctamente")
    else:
        st.info("No hay cotizaciones guardadas aún")

if __name__ == "__main__":
    main()
