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

            # Entrada de usuario para la cantidad de licencias
            cantidad_licencias = st.number_input('Ingresa la cantidad de licencias:', min_value=1, step=1)

            # Filtrar el DataFrame según la cantidad de licencias
            df_filtrado = df_productos[(df_productos['Tier Min'] <= cantidad_licencias) & (df_productos['Tier Max'] >= cantidad_licencias)]

            # Crear el selectbox para 'Term (Month)'
            term_options = [12, 24, 36]
            term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

            # Filtrar el DataFrame según el 'Term (Month)' seleccionado
            df_filtrado = df_filtrado[df_filtrado['Term (Month)'] == term_selected]

            # Definir las categorías disponibles para el selectbox de productos
            categorias = [
                'ThreatDown ADVANCED',
                'ThreatDown ADVANCED SERVER',
                'ThreatDown ELITE',
                'ThreatDown ELITE SERVER',
                'ThreatDown ULTIMATE',
                'ThreatDown ULTIMATE SERVER',
                'MOBILE SECURITY'
            ]

            # Filtrar el DataFrame según las categorías definidas
            df_filtrado = df_filtrado[df_filtrado['Product Title'].isin(categorias)]

            # Verificar si hay productos después de los filtros
            if not df_filtrado.empty:
                # Crear una lista de opciones para el selectbox de productos
                opciones_producto = df_filtrado['Product Title'].tolist()

                # Selectbox para que el usuario seleccione un producto
                producto_seleccionado = st.selectbox('Selecciona un producto:', opciones_producto)

                # Obtener los detalles del producto seleccionado
                detalles_producto = df_filtrado[df_filtrado['Product Title'] == producto_seleccionado].iloc[0]

                # Calcular el subtotal
                subtotal = cantidad_licencias * detalles_producto['MSRP USD']

                # Calcular el IVA (16%)
                iva = subtotal * 0.16

                # Calcular el total
                total = subtotal + iva

                # Mostrar los detalles del producto y los cálculos
                st.write("Detalles del producto seleccionado:")
                st.write(f"**Número de Producto:** {detalles_producto['Product Number']}")
                st.write(f"**Título del Producto:** {detalles_producto['Product Title']}")
                st.write(f"**Descripción del Producto:** {detalles_producto['Product Description']}")
                st.write(f"**Período de Duración:** {detalles_producto['Term (Month)']} meses")
                st.write(f"**Precio Unitario (MSRP USD):** ${detalles_producto['MSRP USD']:.2f}")
                st.write(f"**Cantidad de Licencias:** {cantidad_licencias}")
                st.write(f"**Subtotal:** ${subtotal:.2f}")
                st.write(f"**IVA (16%):** ${iva:.2f}")
                st.write(f"**Total:** ${total:.2f}")
            else:
                st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Term (Month)', 'Product Title', 'Tier Min', 'Tier Max', 'Product Number', 'Product Description' y/o 'MSRP USD'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

