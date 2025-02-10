import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# Cargar datos desde Excel (Asegurar que el archivo está en el mismo directorio o en una ruta accesible)
@st.cache_data
def load_data():
    data = pd.read_excel("precios_threatdown.xlsx").rename(columns=lambda x: x.strip())
    return data

data = load_data()

# Filtrar productos que solo sean ThreatDown
productos_validos = [
    "ThreatDown Core", "ThreatDown Core Server", "ThreatDown Advanced", "ThreatDown Advanced Server",
    "ThreatDown Elite", "ThreatDown Elite Server", "ThreatDown Ultimate", "ThreatDown Ultimate Server",
    "ThreatDown Mobile"
]
data = data[data['Product Title'].isin(productos_validos)]

# Verificar nombres de columnas
st.write("Columnas disponibles en el archivo:", data.columns)
if 'MSRP USD' not in data.columns:
    st.error("Error: La columna 'MSRP USD' no existe en el archivo Excel. Verifica el nombre y vuelve a intentarlo.")

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
    
    # Dropdown para seleccionar productos
    producto_seleccionado = st.selectbox("Selecciona un producto", productos_validos)
    cantidad = st.number_input(f"Cantidad para {producto_seleccionado}", min_value=1, step=1)
    descuento = st.number_input(f"Descuento (%) para {producto_seleccionado}", min_value=0, max_value=100)
    
    # Verificar si el producto tiene precio registrado
    precio_unitario = data.loc[data['Product Title'] == producto_seleccionado, 'MSRP USD']
    if not precio_unitario.empty:
        precio_unitario = precio_unitario.iloc[0] * ((100 - descuento) / 100)
    else:
        st.error(f"No se encontró precio para el producto {producto_seleccionado}. Verifica el archivo de precios.")
        precio_unitario = 0
    
    total = precio_unitario * cantidad
    
    productos_seleccionados = [{"producto": producto_seleccionado, "cantidad": cantidad, "precio_unitario": precio_unitario, "total": total}]
    
    if st.button("Generar Cotización"):
        subtotal = sum(p["total"] for p in productos_seleccionados)
        iva = subtotal * 0.16
        total = subtotal + iva
        
        # Generar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, "Cotización ThreatDown", ln=True, align='C')
        pdf.ln(10)
        pdf.cell(200, 10, f"Ciudad de México a {datetime.datetime.now().strftime('%d')} de {datetime.datetime.now().strftime('%B')} de {datetime.datetime.now().strftime('%Y')}", ln=True, align='R')
        pdf.ln(10)
        pdf.cell(200, 10, f"Para: {cliente}", ln=True)
        pdf.cell(200, 10, f"Empresa: {empresa}", ln=True)
        pdf.ln(10)
        pdf.multi_cell(0, 10, saludo)
        pdf.ln(10)
        pdf.cell(200, 10, "Productos Cotizados:", ln=True)
        for p in productos_seleccionados:
            pdf.cell(200, 10, f"{p['producto']} - {p['cantidad']} unidades - ${p['precio_unitario']:.2f} c/u - Total: ${p['total']:.2f}", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, f"Subtotal: ${subtotal:.2f}", ln=True)
        pdf.cell(200, 10, f"IVA (16%): ${iva:.2f}", ln=True)
        pdf.cell(200, 10, f"Total: ${total:.2f}", ln=True)
        pdf.ln(10)
        pdf.cell(200, 10, "Condiciones Comerciales:", ln=True)
        pdf.multi_cell(0, 10, condiciones)
        pdf.ln(10)
        pdf.cell(200, 10, f"Atentamente: {cotizador}", ln=True)
        pdf.cell(200, 10, f"Puesto: {puesto}", ln=True)
        pdf.output("cotizacion_threatdown.pdf")
        
        st.success("Cotización generada correctamente. Descarga el PDF.")
        with open("cotizacion_threatdown.pdf", "rb") as file:
            st.download_button("Descargar PDF", file, "cotizacion_threatdown.pdf")
else:
    st.error("Acceso denegado")
