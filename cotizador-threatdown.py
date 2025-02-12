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
        columnas_necesarias = ['Term (Month)', 'Product Title', 'Tier Min', 'Tier Max', 'Product Number', 'Product Description', 'MSRP USD']
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
            categorias = ['CORE', 'CORE SERVER', 'ADVANCED', 'ADVANCED SERVER', 'ELITE', 'ELITE SERVER', 'ULTIMATE', 'ULTIMATE SERVER', 'MOBILE']

            # Crear el segundo selectbox para filtrar por categoría
            categoria_selected = st.selectbox('Selecciona la categoría del producto:', options=categorias)

            # Filtrar el DataFrame según la categoría seleccionada
            df_filtrado = df_filtrado[df_filtrado['Product Title'].str.contains(categoria_selected, case=False, na=False)]

            # Input para el filtro numérico basado en 'Tier Min' y 'Tier Max'
            numero = st.number_input('Ingresa un número para filtrar por Tier:', min_value=0, step=1)

            # Filtrar el DataFrame según el número ingresado
            df_filtrado = df_filtrado[(df_filtrado['Tier Min'] <= numero) & (df_filtrado['Tier Max'] >= numero)]

            # Verificar si hay productos después de los filtros
            if not df_filtrado.empty:
                # Crear una lista de opciones para el selectbox de productos
                opciones_producto = df_filtrado['Product Title'].tolist()

                # Selectbox para que el usuario seleccione un producto
                producto_seleccionado = st.selectbox('Selecciona un producto de la lista filtrada:', opciones_producto)

                # Obtener los detalles del producto seleccionado
                detalles_producto = df_filtrado[df_filtrado['Product Title'] == producto_seleccionado]

                # Seleccionar las columnas relevantes para mostrar
                columnas_detalles = ['Product Number', 'Product Title', 'Term (Month)', 'Product Description', 'MSRP USD']

                # Mostrar los detalles del producto en una tabla
                st.write("Detalles del producto seleccionado:")
                st.table(detalles_producto[columnas_detalles])
            else:
                st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Term (Month)', 'Product Title', 'Tier Min', 'Tier Max', 'Product Number', 'Product Description' y/o 'MSRP USD'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

