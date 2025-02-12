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
        columnas_necesarias = ['Tier Min', 'Tier Max', 'Term (Month)', 'Product Title', 'MSRP USD']
        if all(col in df_productos.columns for col in columnas_necesarias):
            # Convertir las columnas 'Tier Min' y 'Tier Max' a numéricas, forzando errores a NaN
            df_productos['Tier Min'] = pd.to_numeric(df_productos['Tier Min'], errors='coerce')
            df_productos['Tier Max'] = pd.to_numeric(df_productos['Tier Max'], errors='coerce')

            # Eliminar filas con NaN en 'Tier Min' o 'Tier Max'
            df_productos = df_productos.dropna(subset=['Tier Min', 'Tier Max'])

            # Entrada de cantidad de licencias
            cantidad_licencias = st.number_input('Ingresa la cantidad de licencias:', min_value=1, step=1)

            # Filtrar productos según la cantidad de licencias
            df_filtrado = df_productos[
                (df_productos['Tier Min'] <= cantidad_licencias) & 
                (df_productos['Tier Max'] >= cantidad_licencias)
            ]

            # Selección del período de duración
            term_options = [12, 24, 36]
            term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

            # Filtrar productos según el período de duración seleccionado
            df_filtrado = df_filtrado[df_filtrado['Term (Month)'] == term_selected]

            # Definir las palabras clave para los productos
            palabras_clave = [
                'ThreatDown ADVANCED',
                'ThreatDown ADVANCED SERVER',
                'ThreatDown ELITE',
                'ThreatDown ELITE SERVER',
                'ThreatDown ULTIMATE',
                'ThreatDown ULTIMATE SERVER',
                'MOBILE SECURITY'
            ]

            # Filtrar productos según las palabras clave
            df_filtrado = df_filtrado[
                df_filtrado['Product Title'].str.contains('|'.join(palabras_clave), case=False, na=False)
            ]

            # Verificar si hay productos después de los filtros
            if not df_filtrado.empty:
                # Crear una lista de opciones para el selectbox de productos
                opciones_producto = df_filtrado['Product Title'].tolist()

                # Selectbox para que el usuario seleccione un producto
                producto_seleccionado = st.selectbox('Selecciona un producto:', opciones_producto)

                # Obtener los detalles del producto seleccionado
                detalles_producto = df_filtrado[df_filtrado['Product Title'] == producto_seleccionado].iloc[0]

                # Calcular el subtotal, IVA y total
                subtotal = cantidad_licencias * detalles_producto['MSRP USD']
                iva = subtotal * 0.16
                total = subtotal + iva

                # Mostrar los resultados
                st.write("**Resumen de la Cotización:**")
                st.write(f"**Producto:** {detalles_producto['Product Title']}")
                st.write(f"**Cantidad de Licencias:** {cantidad_licencias}")
                st.write(f"**Precio Unitario (MSRP USD):** ${detalles_producto['MSRP USD']:.2f}")
                st.write(f"**Subtotal:** ${subtotal:.2f}")
                st.write(f"**IVA (16%):** ${iva:.2f}")
                st.write(f"**Total:** ${total:.2f}")

                # Botón para nueva cotización
                if st.button('Nueva Cotización'):
                    st.experimental_rerun()
            else:
                st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Tier Min', 'Tier Max', 'Term (Month)', 'Product Title' y/o 'MSRP USD'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

