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
        # Definir las opciones de filtrado para 'Product Title'
        opciones_producto = [
            'ThreatDown CORE',
            'ThreatDown CORE SERVER',
            'ThreatDown ADVANCED',
            'ThreatDown ADVANCED SERVER',
            'ThreatDown ELITE',
            'ThreatDown ELITE SERVER',
            'ThreatDown ULTIMATE',
            'ThreatDown ULTIMATE SERVER',
            'MOBILE SECURITY'
        ]

        # Crear selectbox para 'Product Title'
        producto_seleccionado = st.selectbox('Selecciona el producto:', opciones_producto)

        # Crear selectbox para 'Term (Month)'
        term_options = [12, 24, 36]
        term_seleccionado = st.selectbox('Selecciona el período de duración (meses):', term_options)

        # Filtrar el DataFrame según las selecciones
        df_filtrado = df_productos[
            (df_productos['Product Title'].str.contains(producto_seleccionado, case=False, na=False)) &
            (df_productos['Term (Month)'] == term_seleccionado)
        ]

        # Mostrar los resultados filtrados
        if not df_filtrado.empty:
            st.write("Resultados filtrados:")
            st.dataframe(df_filtrado)
        else:
            st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
