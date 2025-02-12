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
    st.title("Filtro de Productos ThreatDown")

    # Cargar datos
    df_productos = cargar_datos()

    if df_productos is not None:
        # Verificar si las columnas necesarias existen
        columnas_necesarias = ['Product Title', 'Term (Month)', 'Tier Min', 'Tier Max', 'MSRP USD']
        if all(col in df_productos.columns for col in columnas_necesarias):
            # Convertir las columnas 'Tier Min' y 'Tier Max' a numéricas, forzando errores a NaN
            df_productos['Tier Min'] = pd.to_numeric(df_productos['Tier Min'], errors='coerce')
            df_productos['Tier Max'] = pd.to_numeric(df_productos['Tier Max'], errors='coerce')

            # Eliminar filas con NaN en 'Tier Min' o 'Tier Max'
            df_productos = df_productos.dropna(subset=['Tier Min', 'Tier Max'])

            # Definir las opciones de 'Product Title' que contienen las palabras clave deseadas
            opciones_producto = [
                'ThreatDown CORE', 'ThreatDown CORE SERVER', 'ThreatDown ADVANCED',
                'ThreatDown ADVANCED SERVER', 'ThreatDown ELITE', 'ThreatDown ELITE SERVER',
                'ThreatDown ULTIMATE', 'ThreatDown ULTIMATE SERVER', 'MOBILE SECURITY'
            ]

            # Filtrar el DataFrame para incluir solo las filas con 'Product Title' deseados
            df_filtrado = df_productos[df_productos['Product Title'].isin(opciones_producto)]

            # Crear un selectbox para que el usuario seleccione el 'Product Title'
            producto_seleccionado = st.selectbox('Selecciona el Producto:', opciones_producto)

            # Filtrar el DataFrame según el 'Product Title' seleccionado
            df_filtrado = df_filtrado[df_filtrado['Product Title'] == producto_seleccionado]

            # Crear un selectbox para que el usuario seleccione el 'Term (Month)'
            term_options = [12, 24, 36]
            term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

            # Filtrar el DataFrame según el 'Term (Month)' seleccionado
            df_filtrado = df_filtrado[df_filtrado['Term (Month)'] == term_selected]

            # Input para que el usuario ingrese la 'Cantidad de Licencias'
            cantidad_licencias = st.number_input('Ingresa la Cantidad de Licencias:', min_value=1, step=1)

            # Filtrar el DataFrame según la 'Cantidad de Licencias' y los valores de 'Tier Min' y 'Tier Max'
            df_filtrado = df_filtrado[
                (df_filtrado['Tier Min'] <= cantidad_licencias) &
                (df_filtrado['Tier Max'] >= cantidad_licencias)
            ]

            # Mostrar los resultados filtrados
            if not df_filtrado.empty:
                st.write("Resultados filtrados:")
                st.dataframe(df_filtrado[['Product Title', 'Term (Month)', 'Tier Min', 'Tier Max', 'MSRP USD']])
            else:
                st.warning("No se encontraron productos que coincidan con los filtros aplicados.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Product Title', 'Term (Month)', 'Tier Min', 'Tier Max' y/o 'MSRP USD'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

