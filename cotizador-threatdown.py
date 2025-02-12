import streamlit as st
import pandas as pd

def cargar_datos():
    ruta_archivo = 'precios_threatdown.xlsx'  # Asegúrate de que la ruta sea correcta
    try:
        df = pd.read_excel(ruta_archivo, engine='openpyxl')
        return df
    except FileNotFoundError:
        st.error(f"El archivo {ruta_archivo} no se encontró. Por favor, verifica la ruta.")
        return None

def main():
    st.title("Filtro de Productos ThreatDown")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Definir las opciones de 'Product Title' que contienen las palabras clave deseadas
        palabras_clave = [
            'ThreatDown CORE', 'ThreatDown CORE SERVER', 'ThreatDown ADVANCED',
            'ThreatDown ADVANCED SERVER', 'ThreatDown ELITE', 'ThreatDown ELITE SERVER',
            'ThreatDown ULTIMATE', 'ThreatDown ULTIMATE SERVER', 'MOBILE SECURITY'
        ]

        # Filtrar el DataFrame para incluir solo los productos con las palabras clave
        df_filtrado = df_productos[df_productos['Product Title'].str.contains('|'.join(palabras_clave), case=False, na=False)]

        # Crear el selectbox para 'Product Title'
        producto_seleccionado = st.selectbox('Selecciona el producto:', options=sorted(df_filtrado['Product Title'].unique()))

        # Crear el selectbox para 'Term (Month)'
        term_options = [12, 24, 36]
        term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

        # Filtrar el DataFrame según las selecciones del usuario
        df_resultado = df_filtrado[
            (df_filtrado['Product Title'] == producto_seleccionado) &
            (df_filtrado['Term (Month)'] == term_selected)
        ]

        # Mostrar los resultados
        if not df_resultado.empty:
            st.write("Detalles del producto seleccionado:")
            st.dataframe(df_resultado)
        else:
            st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

