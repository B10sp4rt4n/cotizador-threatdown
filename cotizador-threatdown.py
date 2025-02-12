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
    st.title("Cotizador de Productos")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Verificar si las columnas necesarias existen
        columnas_necesarias = ['Term (Month)', 'Product Title', 'Tier Min', 'Tier Max']
        if all(col in df_productos.columns for col in columnas_necesarias):
            # Convertir las columnas 'Tier Min' y 'Tier Max' a numéricas, forzando errores a NaN
            df_productos['Tier Min'] = pd.to_numeric(df_productos['Tier Min'], errors='coerce')
            df_productos['Tier Max'] = pd.to_numeric(df_productos['Tier Max'], errors='coerce')

            # Eliminar filas con NaN en 'Tier Min' o 'Tier Max'
            df_productos = df_productos.dropna(subset=['Tier Min', 'Tier Max'])

            # Crear el primer selectbox para 'Term (Month)'
            term_options = [12, 24, 36]
            term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

            # Filtrar el DataFrame según el 'Term (Month)' seleccionado
            df_filtrado = df_productos[df_productos['Term (Month)'] == term_selected]

            # Definir las categorías disponibles para el segundo selectbox
            categorias = ['CORE', 'ADVANCED', 'ELITE', 'ULTIMATE', 'MOBILE']

            # Crear el segundo selectbox para filtrar por categoría
            categoria_selected = st.selectbox('Selecciona la categoría del producto:', options=categorias)

            # Filtrar el DataFrame según la categoría seleccionada
            df_filtrado = df_filtrado[df_filtrado['Product Title'].str.contains(categoria_selected, case=False, na=False)]

            # Input para el filtro numérico basado en 'Tier Min' y 'Tier Max'
            numero = st.number_input('Ingresa un número para filtrar por Tier:', min_value=0, step=1)

            # Filtrar el DataFrame según el número ingresado
            df_filtrado = df_filtrado[(df_filtrado['Tier Min'] <= numero) & (df_filtrado['Tier Max'] >= numero)]

            # Mostrar los datos filtrados
            st.write(f"Productos con un período de {term_selected} meses, categoría '{categoria_selected}' y Tier que incluye el número {numero}:")
            st.dataframe(df_filtrado)
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Term (Month)', 'Product Title', 'Tier Min' y/o 'Tier Max'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
