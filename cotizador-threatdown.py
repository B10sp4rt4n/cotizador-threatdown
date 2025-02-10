import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# Cargar datos desde Excel (Asegurar que el archivo está en el mismo directorio o en una ruta accesible)
@st.cache_data
def load_data():
    return pd.read_excel("precios_threatdown.xlsx")

data = load_data()

# Filtrar productos válidos
productos_validos = ["ThreatDown Advanced", "Advanced Server", "Core", "Core Server", "Elite", "Elite Server", "Ultimate", "Ultimate Server", "Mobile"]
data = data[data['Product Title'].str.contains('|'.join(productos_validos), na=False)]

def generar_pdf(cliente, empresa, saludo, productos, subtotal, iva, total, condiciones, cotizador, puesto):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", style='B', size=12)
    pdf.cell(200, 10, "Cotización ThreatDown", ln=True, align='C')
    pdf.image("logo_empresa.png", x=10, y=8, w=40)
    
    # Fecha
    fecha_actual = datetime.datetime.now()
    fecha_formateada = f"Ciudad de México a {fecha_actual.strftime('%d')} de {fecha_actual.strftime('%B')} de {fecha_actual.strftime('%Y')}"
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, fecha_formateada, ln=True, align='R')
    pdf.ln(10)
    
    # Datos del destinatario
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(200, 10, f"Para: {cliente}", ln=True)
    pdf.cell(200, 10, f"Empresa: {empresa}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, saludo)
    pdf.ln(10)
    
    # Tabla de productos
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(80, 10, "Producto", 1)
    pdf.cell(30, 10, "Cantidad", 1)
    pdf.cell(30, 10, "Precio Unitario", 1)
    pdf.cell(30, 10, "Total", 1)
    pdf.ln()
    pdf.set_font("Arial", size=10)
    for p in productos:
        pdf.cell(80, 10, p["producto"], 1)
        pdf.cell(30, 10, str(p["cantidad"]), 1)
        pdf.cell(30, 10, f"${p['precio_unitario']:.2f}", 1)
        pdf.cell(30, 10, f"${p['total']:.2f}", 1)
        pdf.ln()
    
    # Resumen final
    pdf.ln(5)
    pdf.cell(200, 10, f"Subtotal: ${subtotal:.2f}", ln=True, align='R')
    pdf.cell(200, 10, f"IVA (16%): ${iva:.2f}", ln=True, align='R')
    pdf.cell(200, 10, f"Total: ${total:.2f}", ln=True, align='R')
    pdf.ln(10)
    
    # Condiciones comerciales
    pdf.set_font("Arial", style='B', size=10)
    pdf.cell(200, 10, "Condiciones Comerciales:", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, condiciones)
    pdf.ln(10)
    
    # Datos del cotizador
    pdf.cell(200, 10, f"Atentamente: {cotizador}", ln=True)
    pdf.cell(200, 10, f"Puesto: {puesto}", ln=True)
    
    # Logo de ThreatDown
    pdf.image("logo_threatdown.png", x=160, y=pdf.get_y() + 5, w=30)
    
    pdf.output("cotizacion_threatdown.pdf")

# Streamlit UI
st.title("Cotizador ThreatDown")

usuario = st.text_input("Usuario")
password = st.text_input("Contraseña", type="password")
if usuario == "admin" and password == "1234":
    cliente = st.text_input("Nombre del cliente")
    empresa = st.text_input("Empresa del cliente")
    saludo = st.text_area("Mensaje de saludo")
    condiciones = st.text_area("Condiciones comerciales")
    cotizador = st.text_input("Nombre del que cotiza")
    puesto = st.text_input("Puesto del que cotiza")
    
    productos_seleccionados = []
    for index, row in data.iterrows():
        if st.checkbox(row['Product Title']):
            cantidad = st.number_input(f"Cantidad para {row['Product Title']}", min_value=int(row['Tier Min']), max_value=int(row['Tier Max']), step=1)
            descuento = st.number_input(f"Descuento (%) para {row['Product Title']}", min_value=0, max_value=100)
            precio_unitario = row['MSRP'] * ((100 - descuento) / 100)
            total = precio_unitario * cantidad
            productos_seleccionados.append({"producto": row['Product Title'], "cantidad": cantidad, "precio_unitario": precio_unitario, "total": total})
    
    if st.button("Generar Cotización"):
        subtotal = sum(p["total"] for p in productos_seleccionados)
        iva = subtotal * 0.16
        total = subtotal + iva
        generar_pdf(cliente, empresa, saludo, productos_seleccionados, subtotal, iva, total, condiciones, cotizador, puesto)
        st.success("Cotización generada correctamente. Descarga el PDF.")
        with open("cotizacion_threatdown.pdf", "rb") as file:
            st.download_button("Descargar PDF", file, "cotizacion_threatdown.pdf")
else:
    st.error("Acceso denegado")

