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
        if 'Term (Month)' in df_productos.columns and 'Product Title' in df_productos.columns:
            # Crear un selectbox para el período de duración
            periodo = st.selectbox(
                'Selecciona el período de duración (meses):',
                options=[12, 24, 26]
            )

            # Definir las palabras clave para filtrar
            palabras_clave = ['CORE', 'CORE SERVER', 'ADVANCED', 'ADVANCED SERVER', 'ELITE', 'ELITE SERVER', 'ULTIMATE', 'ULTIMATE SERVER', 'MOBILE']
            patron_busqueda = '|'.join(palabras_clave)

            # Filtrar el DataFrame según el período seleccionado y las palabras clave en 'Product Title'
            df_filtrado = df_productos[
                (df_productos['Term (Month)'] == periodo) &
                (df_productos['Product Title'].str.contains(patron_busqueda, case=False, na=False))
            ]

            # Mostrar los datos filtrados
            st.write(f"Productos con un período de {periodo} meses y títulos que contienen las palabras clave:")
            st.dataframe(df_filtrado)
        else:
            st.error("Las columnas 'Term (Month)' y/o 'Product Title' no se encuentran en el archivo.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
