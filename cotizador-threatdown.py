import streamlit as st
import pandas as pd

# Cargar datos desde el archivo Excel
@st.cache_data
def cargar_datos(ruta_archivo):
    df = pd.read_excel(ruta_archivo, engine='openpyxl')
    return df

# Función para filtrar productos según la búsqueda
def filtrar_productos(df, consulta):
    consulta = consulta.lower()
    filtrado = df[df['Nombre del Producto'].str.contains(consulta, case=False) |
                  df['Descripción'].str.contains(consulta, case=False)]
    return filtrado

def main():
    st.title("Cotizador de Productos")

    # Ruta del archivo Excel
    ruta_archivo = 'ruta/a/tu/archivo.xlsx'

    # Cargar datos
    df_productos = cargar_datos(ruta_archivo)

    # Campo de búsqueda
    consulta = st.text_input("Buscar producto por nombre o descripción:")

    if consulta:
        # Filtrar productos
        resultados = filtrar_productos(df_productos, consulta)

        if not resultados.empty:
            st.write(f"Se encontraron {len(resultados)} productos:")
            st.dataframe(resultados)
        else:
            st.write("No se encontraron productos que coincidan con la búsqueda.")
    else:
        st.write("Por favor, ingresa un término de búsqueda.")

if __name__ == "__main__":
    main()


