import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# Cargar datos desde Excel
@st.cache_data
def load_data():
    data = pd.read_excel("precios_threatdown.xlsx").rename(columns=lambda x: x.strip())
    return data

data = load_data()

# Filtrar productos válidos
productos_validos = [
    "ThreatDown Core", "ThreatDown Core Server", "ThreatDown Advanced", "ThreatDown Advanced Server",
    "ThreatDown Elite", "ThreatDown Elite Server", "ThreatDown Ultimate", "ThreatDown Ultimate Server",
    "ThreatDown Mobile"
]
data = data[data['Product Title'].isin(productos_validos)]

# Verificar nombres de columnas
required_columns = ['Product Title', 'License Type', 'Tier Min', 'Tier Max', 'MSRP USD']
missing_columns = [col for col in required_columns if col not in data.columns]
if missing_columns:
    st.error(f"Error: Las siguientes columnas faltan en el archivo Excel: {', '.join(missing_columns)}")
else:
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
        
        # Dropdown para seleccionar producto y tipo de licencia
        producto_seleccionado = st.selectbox("Selecciona un producto", productos_validos)
        tipos_licencia = data[data['Product Title'] == producto_seleccionado]['License Type'].unique()
        tipo_licencia_seleccionado = st.selectbox("Selecciona el tipo de licencia", tipos_licencia)
        
        cantidad = st.number_input(f"Cantidad para {producto_seleccionado}", min_value=1, step=1)
        descuento = st.number_input(f"Descuento (%) para {producto_seleccionado}", min_value=0, max_value=100)
        duracion = st.selectbox("Duración de la licencia (meses)", [12, 24, 36])
        
        # Filtrar el precio correspondiente
        precio_filtro = data[
            (data['Product Title'] == producto_seleccionado) &
            (data['License Type'] == tipo_licencia_seleccionado) &
            (data['Tier Min'] <= cantidad) &
            (data['Tier Max'] >= cantidad)
        ]
        
        if not precio_filtro.empty:
            precio_base = precio_filtro.iloc[0]['MSRP USD']
            
            # Ajustar el precio según la duración de la licencia
            if duracion == 12:
                factor_duracion = 1.0  # Sin descuento
            elif duracion == 24:
                factor_duracion = 0.95  # 5% de descuento
            elif duracion == 36:
                factor_duracion = 0.90  # 10% de descuento
            else:
                factor_duracion = 1.0  # Por defecto, sin descuento
            
            precio_ajustado = precio_base * factor_duracion
            precio_unitario = precio_ajustado * ((100 - descuento) / 100)
            total = precio_unitario * cantidad
            
            productos_seleccionados = [{
                "producto": producto_seleccionado,
                "tipo_licencia": tipo_licencia_seleccionado,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "total": total
            }]
            
            if st.button("Generar Cotización"):
                subtotal = sum(p["total"] for p in productos_seleccionados)
                iva = subtotal * 0.16
                total_final = subtotal + iva
                
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
                    pdf.cell(200, 10, f"{p['producto']} ({p['tipo_licencia']}) - {p['cantidad']} unidades - ${p['precio_unitario']:.2f} c/u - Total: ${p['total']:.2f}", ln=True)
                pdf.ln(10)
                pdf.cell(200, 10, f"Subtotal: ${subtotal:.2f}", ln=True)
                pdf.cell(200, 10, f"IVA (16%): ${iva:.2f}", ln=True)
                pdf.cell(200, 10, f"Total: ${total_final:.2f}", ln=True)
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
            st.error("No se encontró un precio para la combinación seleccionada de producto, tipo de licencia y cantidad.")
    else:
        st.error("Acceso denegado")

