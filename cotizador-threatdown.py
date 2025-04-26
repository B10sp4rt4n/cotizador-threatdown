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
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cotizaciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT, contacto TEXT, propuesta TEXT,
                fecha TEXT, responsable TEXT, 
                total_lista REAL, total_costo REAL, total_venta REAL,
                utilidad REAL, margen REAL,
                vigencia TEXT, condiciones_comerciales TEXT
            )""")
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
# Generador de PDF
# ========================
class CotizacionPDF(FPDF):
    def header(self):
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, x=10, y=8, w=40)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Cliente: {self.cliente}", ln=True)
        self.cell(0, 10, f"Contacto: {self.contacto}", ln=True)
        self.cell(0, 10, f"Propuesta: {self.propuesta}", ln=True)
        self.cell(0, 10, f"Vigencia: {self.vigencia}", ln=True)
        self.ln(10)
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "Cotización Comercial", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-40)
        self.set_font("Helvetica", "I", 10)
        self.multi_cell(0, 5, f"Condiciones Comerciales:\n{self.condiciones}")
        self.ln(5)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Responsable: {self.responsable}", ln=True)
        if os.path.exists("firma_synappssys.png"):
            self.image("firma_synappssys.png", x=50, y=self.get_y(), w=100)
        self.cell(0, 10, "SynAppsSys", 0, 0, "C")

    def tabla_productos(self, data):
        self.set_font("Helvetica", "B", 10)
        headers = ["Cantidad", "Producto", "Periodo", "P. Unitario", "P. Lista", "Descuento %", "P. Final"]
        col_widths = [20, 60, 25, 25, 25, 25, 25]
        for header, width in zip(headers, col_widths):
            self.cell(width, 10, header, 1, 0, "C")
        self.ln()

        self.set_font("Helvetica", "", 10)
        total = 0
        for item in data:
            self.cell(col_widths[0], 10, str(item["cantidad"]), 1, 0, "C")
            self.cell(col_widths[1], 10, item["producto"], 1)
            self.cell(col_widths[2], 10, f"{self.periodo} meses", 1, 0, "C")
            self.cell(col_widths[3], 10, f"${item['precio_venta']:.2f}", 1, 0, "R")
            self.cell(col_widths[4], 10, f"${item['precio_lista']:.2f}", 1, 0, "R")
            self.cell(col_widths[5], 10, f"{item['descuento_venta']:.1f}%", 1, 0, "C")
            self.cell(col_widths[6], 10, f"${item['total_venta']:.2f}", 1, 0, "R")
            self.ln()
            total += item["total_venta"]

        self.set_font("Helvetica", "B", 10)
        self.cell(sum(col_widths[:-1]), 10, "TOTAL:", 1, 0, "R")
        self.cell(col_widths[-1], 10, f"${total:.2f}", 1, 0, "R")

# ========================
# Lógica principal
# ========================
def main():
    inicializar_db()
    datos = mostrar_encabezado()
    df_precios = cargar_datos()

    termino = st.selectbox("📅 Plazo de servicio (meses):", options=sorted(df_precios["Term (Month)"].dropna().unique()))

    df_filtrado = df_precios[df_precios["Term (Month)"] == termino]
    productos = df_filtrado["Product Title"].unique()
    seleccionados = st.multiselect("🔍 Seleccionar productos", productos)

    detalle = []
    for producto in seleccionados:
        st.divider()
        st.subheader(f"📦 {producto}")

        df_producto = df_filtrado[df_filtrado["Product Title"] == producto]
        cantidad = st.number_input(f"Cantidad", min_value=1, value=1, key=f"cant_{producto}")

        rango_valido = df_producto[(df_producto["Tier Min"] <= cantidad) & (df_producto["Tier Max"] >= cantidad)]
        if rango_valido.empty:
            st.error("⛔ Cantidad fuera de rango válido")
            continue

        precio_lista = rango_valido.iloc[0]["MSRP USD"]

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
            venta_disc = st.number_input("Descuento Venta (%)", 0.0, max_venta_disc, 0.0, key=f"venta_{producto}")

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
        st.divider()
        st.subheader("📊 Resumen Financiero")

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Lista", f"${df['total_lista'].sum():,.2f}")
        col2.metric("Total Costo", f"${df['total_costo'].sum():,.2f}", delta=f"-{df['descuento_costo'].mean():.1f}% descuento costo")
        col3.metric("Total Venta", f"${df['total_venta'].sum():,.2f}", delta=f"-{df['descuento_venta'].mean():.1f}% descuento venta")

        utilidad = df['total_venta'].sum() - df['total_costo'].sum()
        margen = (utilidad / df['total_venta'].sum()) * 100 if df['total_venta'].sum() > 0 else 0
        st.success(f"## 🏆 Resultado Final: Utilidad ${utilidad:,.2f} | Margen {margen:.1f}%")

        if st.button("💾 Guardar Cotización", type="primary"):
            with conectar_db() as conn:
                cursor = conn.cursor()
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

    st.divider()
    st.subheader("📂 Historial de Cotizaciones")

    with conectar_db() as conn:
        df_historial = pd.read_sql_query("SELECT * FROM cotizaciones ORDER BY fecha DESC", conn)

    if not df_historial.empty:
        opciones = [
            f"{row['fecha']} - {row['cliente']} - {row['propuesta']} (${row['total_venta']:,.2f})"
            for _, row in df_historial.iterrows()
        ]
        seleccion = st.selectbox("Seleccionar cotización:", opciones)

        if seleccion:
            index = opciones.index(seleccion)
            id_cotizacion = df_historial.iloc[index]['id']

            detalle_cotizacion = pd.read_sql_query(
                f"""
                SELECT producto, cantidad, precio_lista, descuento_costo, costo, descuento_venta, precio_venta
                FROM detalle_productos WHERE cotizacion_id = {id_cotizacion}
                """, conn)

            st.subheader("📄 Detalles de la Cotización")
            st.dataframe(detalle_cotizacion)

            if st.button("📄 Generar PDF"):
                pdf = CotizacionPDF()
                pdf.cliente = df_historial.iloc[index]['cliente']
                pdf.contacto = df_historial.iloc[index]['contacto']
                pdf.propuesta = df_historial.iloc[index]['propuesta']
                pdf.vigencia = df_historial.iloc[index]['vigencia']
                pdf.condiciones = df_historial.iloc[index]['condiciones_comerciales']
                pdf.responsable = df_historial.iloc[index]['responsable']
                pdf.periodo = termino
                pdf.add_page()

                detalle_pdf = []
                for _, row in detalle_cotizacion.iterrows():
                    detalle_pdf.append({
                        "cantidad": row['cantidad'],
                        "producto": row['producto'],
                        "precio_venta": row['precio_venta'],
                        "precio_lista": row['precio_lista'],
                        "descuento_venta": row['descuento_venta'],
                        "total_venta": row['precio_venta'] * row['cantidad']
                    })
                pdf.tabla_productos(detalle_pdf)

                pdf_output = f"cotizacion_{id_cotizacion}.pdf"
                pdf.output(pdf_output)

                with open(pdf_output, "rb") as f:
                    st.download_button("⬇️ Descargar PDF Final", data=f, file_name=pdf_output, mime="application/pdf")
    else:
        st.info("No hay cotizaciones guardadas en el historial")

if __name__ == "__main__":
    main()
