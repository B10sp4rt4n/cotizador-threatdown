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
    st.title("Selección de Producto")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Verificar si la columna 'Product Title' existe
        if 'Product Title' in df_productos.columns:
            # Eliminar filas con valores nulos en 'Product Title' y duplicados
            df_productos = df_productos.dropna(subset=['Product Title']).drop_duplicates(subset=['Product Title'])

            # Obtener la lista de títulos de productos
            lista_productos = df_productos['Product Title'].tolist()

            # Crear el selectbox para seleccionar un producto
            producto_seleccionado = st.selectbox('Selecciona un producto de la lista:', lista_productos)

            # Mostrar detalles adicionales del producto seleccionado
            detalles_producto = df_productos[df_productos['Product Title'] == producto_seleccionado]
            st.write("Detalles del producto seleccionado:")
            st.dataframe(detalles_producto)
        else:
            st.error("La columna 'Product Title' no se encuentra en el archivo.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
