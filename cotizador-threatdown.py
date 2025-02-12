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
    st.title("Selector de Productos")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Verificar si la columna 'Product Title' existe
        if 'Product Title' in df_productos.columns:
            # Definir las palabras clave
            palabras_clave = ['CORE', 'CORE SERVER', 'ADVANCED', 'ADVANCED SERVER', 'ELITE', 'ELITE SERVER', 'ULTIMATE', 'ULTIMATE SERVER', 'MOBILE']

            # Filtrar los productos que contienen alguna de las palabras clave
            filtro = df_productos['Product Title'].str.contains('|'.join(palabras_clave), case=False, na=False)
            productos_filtrados = df_productos[filtro]

            if not productos_filtrados.empty:
                # Crear una lista de opciones para el selectbox
                opciones_producto = productos_filtrados['Product Title'].unique().tolist()

                # Selectbox para que el usuario seleccione un producto
                producto_seleccionado = st.selectbox('Selecciona un producto:', opciones_producto)

                # Obtener los detalles del producto seleccionado
                detalles_producto = productos_filtrados[productos_filtrados['Product Title'] == producto_seleccionado]

                # Seleccionar las columnas relevantes para mostrar
                columnas_detalles = ['Product Number', 'Product Title', 'Term (Month)', 'Product Description', 'MSRP USD']

                # Mostrar los detalles del producto en una tabla
                st.write("Detalles del producto seleccionado:")
                st.table(detalles_producto[columnas_detalles])
            else:
                st.warning("No se encontraron productos que coincidan con las palabras clave proporcionadas.")
        else:
            st.error("La columna 'Product Title' no se encuentra en el archivo.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
