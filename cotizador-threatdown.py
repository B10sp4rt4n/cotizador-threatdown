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
        # Verificar si la columna 'Product Title' existe
        if 'Product Title' in df_productos.columns:
            # Definir las opciones de licencia disponibles
            opciones_licencia = ['CORE', 'ADVANCED', 'ELITE', 'ULTIMATE', 'MOBILE']

            # Crear un selectbox para que el usuario seleccione la opción de licencia
            licencia_seleccionada = st.selectbox(
                'Selecciona la opción de licencia:',
                options=opciones_licencia
            )

            # Filtrar el DataFrame según la opción de licencia seleccionada
            df_filtrado = df_productos[df_productos['Product Title'].str.contains(licencia_seleccionada, case=False, na=False)]

            # Mostrar los datos filtrados
            st.write(f"Productos con la opción de licencia '{licencia_seleccionada}':")
            st.dataframe(df_filtrado)
        else:
            st.error("La columna 'Product Title' no se encuentra en el archivo.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

