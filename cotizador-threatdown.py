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
        # Verificar si la columna 'Term (Month)' existe
        if 'Term (Month)' in df_productos.columns:
            # Crear un selectbox para el período de duración
            periodo = st.selectbox(
                'Selecciona el período de duración (meses):',
                options=[12, 24, 26]
            )

            # Filtrar el DataFrame según el período seleccionado
            df_filtrado = df_productos[df_productos['Term (Month)'] == periodo]

            # Mostrar los datos filtrados
            st.write(f"Productos con un período de {periodo} meses:")
            st.dataframe(df_filtrado)
        else:
            st.error("La columna 'Term (Month)' no se encuentra en el archivo.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()

