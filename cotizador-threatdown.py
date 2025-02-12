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
    st.title("Cotizador de Licencias")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Verificar si las columnas necesarias existen
        columnas_necesarias = ['Tier Min', 'Tier Max', 'Term (Month)', 'Product Title', 'MSRP USD']
        if all(col in df_productos.columns for col in columnas_necesarias):
            # Convertir las columnas 'Tier Min', 'Tier Max' y 'MSRP USD' a numéricas
            df_productos['Tier Min'] = pd.to_numeric(df_productos['Tier Min'], errors='coerce')
            df_productos['Tier Max'] = pd.to_numeric(df_productos['Tier Max'], errors='coerce')
            df_productos['MSRP USD'] = pd.to_numeric(df_productos['MSRP USD'], errors='coerce')

            # Eliminar filas con NaN en 'Tier Min', 'Tier Max' o 'MSRP USD'
            df_productos = df_productos.dropna(subset=['Tier Min', 'Tier Max', 'MSRP USD'])

            # Entrada de cantidad de licencias
            cantidad_licencias = st.number_input('Ingresa la cantidad de licencias:', min_value=1, step=1)

            # Filtrar productos que coincidan con la cantidad de licencias
            df_filtrado = df_productos[
                (df_productos['Tier Min'] <= cantidad_licencias) &
                (df_productos['Tier Max'] >= cantidad_licencias)
            ]

            if not df_filtrado.empty:
                # Selector de período de duración
                term_options = [12, 24, 36]
                term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

                # Filtrar por 'Term (Month)'
                df_filtrado = df_filtrado[df_filtrado['Term (Month)'] == term_selected]

                if not df_filtrado.empty:
                    # Definir las opciones de productos
                    productos_disponibles = [
                        'ThreatDown ADVANCED',
                        'ThreatDown ADVANCED SERVER',
                        'ThreatDown ELITE',
                        'ThreatDown ELITE SERVER',
                        'ThreatDown ULTIMATE',
                        'ThreatDown ULTIMATE SERVER',
                        'MOBILE SECURITY'
                    ]

                    # Filtrar productos disponibles
                    df_filtrado = df_filtrado[
                        df_filtrado['Product Title'].str.contains('|'.join(productos_disponibles), case=False, na=False)
                    ]

                    if not df_filtrado.empty:
                        # Selector de producto
                        producto_selected = st.selectbox('Selecciona el producto:', df_filtrado['Product Title'].unique())

                        # Obtener los detalles del producto seleccionado
                        producto_detalles = df_filtrado[df_filtrado['Product Title'] == producto_selected].iloc[0]

                        # Calcular el subtotal
                        subtotal = cantidad_licencias * producto_detalles['MSRP USD']

                        # Calcular el IVA (16%)
                        iva = subtotal * 0.16

                        # Calcular el total
                        total = subtotal + iva

                        # Mostrar los resultados
                        st.write("### Detalles de la Cotización")
                        st.write(f"**Producto:** {producto_selected}")
                        st.write(f"**Cantidad de Licencias:** {cantidad_licencias}")
                        st.write(f"**Período de Duración:** {term_selected} meses")
                        st.write(f"**Precio Unitario (MSRP USD):** ${producto_detalles['MSRP USD']:.2f}")
                        st.write(f"**Subtotal:** ${subtotal:.2f}")
                        st.write(f"**IVA (16%):** ${iva:.2f}")
                        st.write(f"**Total:** ${total:.2f}")
                    else:
                        st.warning("No se encontraron productos disponibles para los criterios seleccionados.")
                else:
                    st.warning("No se encontraron productos para el período de duración seleccionado.")
            else:
                st.warning("No se encontraron productos que coincidan con la cantidad de licencias ingresada.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Tier Min', 'Tier Max', 'Term (Month)', 'Product Title' y/o 'MSRP USD'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
