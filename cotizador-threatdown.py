import pandas as pd
import streamlit as st
import requests
from io import BytesIO

st.title("Cotizador ThreatDown")

# URL directa al archivo en GitHub (versión RAW)
url_excel = "https://raw.githubusercontent.com/B10sp4rt4n/cotizador-threatdown/main/Lista%20de%20Precios%20ThD.xlsx"

# Descargar el archivo
@st.cache_data
def load_data():
    response = requests.get(url_excel)
    if response.status_code == 200:
        return pd.read_excel(BytesIO(response.content), sheet_name="Table003 (Page 21-64)")
    else:
        st.error("No se pudo descargar el archivo Excel. Verifica la URL.")
        return None

df = load_data()

if df is not None:
    st.write("Archivo cargado correctamente")
    st.dataframe(df)

    st.dataframe(df_cotizacion)
else:
    st.write("No se han seleccionado productos para cotizar.")
