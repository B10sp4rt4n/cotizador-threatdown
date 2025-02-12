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
    st.title("Lista Completa de Productos")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Mostrar la lista completa de productos
        st.write("A continuación se muestra la lista completa de productos:")
        st.dataframe(df_productos)
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
