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
    st.title("Filtrado de Productos por Título")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Definir las palabras clave para el filtrado
        palabras_clave = ["CORE", "CORE SERVER", "ADVANCED", "ADVANCED SERVER", 
                          "ELITE", "ELITE SERVER", "ULTIMATE", "ULTIMATE SERVER", "MOBILE"]

        # Crear una expresión regular que combine todas las palabras clave
        patron = '|'.join(palabras_clave)

        # Filtrar el DataFrame para incluir solo los productos cuyos títulos contienen las palabras clave
        df_filtrado = df_productos[df_productos['Product Title'].str.contains(patron, case=False, na=False)]

        # Verificar si hay productos después del filtrado
        if not df_filtrado.empty:
            st.write("Productos que coinciden con las palabras clave especificadas:")
            st.dataframe(df_filtrado)
        else:
            st.warning("No se encontraron productos que coincidan con las palabras clave especificadas.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
