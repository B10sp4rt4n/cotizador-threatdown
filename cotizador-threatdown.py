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
    st.title("Filtro de Productos por Categoría y Período")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Verificar si las columnas necesarias existen
        columnas_necesarias = ['Product Title', 'Term (Month)']
        if all(col in df_productos.columns for col in columnas_necesarias):
            # Definir las categorías disponibles
            categorias = ['CORE', 'CORE SERVER', 'ADVANCED', 'ADVANCED SERVER', 'ELITE', 'ELITE SERVER', 'ULTIMATE', 'ULTIMATE SERVER', 'MOBILE']

            # Crear el selectbox para filtrar por categoría
            categoria_selected = st.selectbox('Selecciona la categoría del producto:', options=categorias)

            # Filtrar el DataFrame según la categoría seleccionada
            df_filtrado = df_productos[df_productos['Product Title'].str.contains(categoria_selected, case=False, na=False)]

            # Crear el selectbox para 'Term (Month)'
            term_options = [12, 24, 36]
            term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

            # Filtrar el DataFrame según el 'Term (Month)' seleccionado
            df_filtrado = df_filtrado[df_filtrado['Term (Month)'] == term_selected]

            # Verificar si hay productos después de los filtros
            if not df_filtrado.empty:
                # Mostrar los productos filtrados
                st.write(f"Productos en la categoría '{categoria_selected}' con un período de {term_selected} meses:")
                st.dataframe(df_filtrado)
            else:
                st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Product Title' y/o 'Term (Month)'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
