import streamlit as st
import pandas as pd

# Cargar los datos desde tu archivo Excel
df = pd.read_excel('precios_threatdown.xlsx', engine='openpyxl')

def main():
    st.title("Cotizador de Productos")

    # Verificar si la columna 'Term (Month)' existe en el DataFrame
    if 'Term (Month)' in df.columns:
        # Obtener los valores mínimo y máximo de la columna 'Term (Month)'
        min_term = int(df['Term (Month)'].min())
        max_term = int(df['Term (Month)'].max())

        # Crear un slider para seleccionar el rango de duración
        term_range = st.slider(
            'Selecciona el rango de duración en meses',
            min_value=min_term,
            max_value=max_term,
            value=(min_term, max_term)
        )

        # Filtrar el DataFrame según el rango seleccionado
        filtered_df = df[df['Term (Month)'].between(term_range[0], term_range[1])]

        # Mostrar el DataFrame filtrado
        st.write("Productos filtrados por duración:")
        st.dataframe(filtered_df)
    else:
        st.error("La columna 'Term (Month)' no se encuentra en el archivo Excel.")

if __name__ == "__main__":
    main()
