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
        columnas_necesarias = ['Product Title', 'Term (Month)', 'Tier Min', 'Tier Max', 'MSRP USD']
        if all(col in df_productos.columns for col in columnas_necesarias):
            # Filtrar los productos disponibles
            productos_disponibles = [
                'ThreatDown ADVANCED',
                'ThreatDown ADVANCED SERVER',
                'ThreatDown ELITE',
                'ThreatDown ELITE SERVER',
                'ThreatDown ULTIMATE',
                'ThreatDown ULTIMATE SERVER',
                'MOBILE SECURITY'
            ]

            # Crear selectbox para seleccionar el producto
            producto_seleccionado = st.selectbox('Selecciona un producto:', productos_disponibles)

            # Filtrar el DataFrame según el producto seleccionado
            df_producto = df_productos[df_productos['Product Title'] == producto_seleccionado]

            # Crear selectbox para seleccionar el período de duración
            term_options = [12, 24, 36]
            term_selected = st.selectbox('Selecciona el período de duración (meses):', options=term_options)

            # Filtrar el DataFrame según el 'Term (Month)' seleccionado
            df_producto = df_producto[df_producto['Term (Month)'] == term_selected]

            if not df_producto.empty:
                # Obtener los valores de 'Tier Min' y 'Tier Max'
                tier_min = df_producto['Tier Min'].values[0]
                tier_max = df_producto['Tier Max'].values[0]

                # Input para la cantidad de licencias
                cantidad_licencias = st.number_input(
                    f'Ingresa la cantidad de licencias (entre {tier_min} y {tier_max}):',
                    min_value=int(tier_min),
                    max_value=int(tier_max),
                    step=1
                )

                # Calcular el subtotal
                msrp_usd = df_producto['MSRP USD'].values[0]
                subtotal = cantidad_licencias * msrp_usd

                # Calcular el IVA (16%)
                iva = subtotal * 0.16

                # Calcular el gran total
                gran_total = subtotal + iva

                # Mostrar los resultados
                st.write("### Detalles de la Cotización")
                st.write(f"**Producto:** {producto_seleccionado}")
                st.write(f"**Período de Duración:** {term_selected} meses")
                st.write(f"**Cantidad de Licencias:** {cantidad_licencias}")
                st.write(f"**Precio Unitario (MSRP USD):** ${msrp_usd:,.2f}")
                st.write(f"**Subtotal:** ${subtotal:,.2f}")
                st.write(f"**IVA (16%):** ${iva:,.2f}")
                st.write(f"**Gran Total:** ${gran_total:,.2f}")
            else:
                st.warning("No se encontraron productos que coincidan con el período de duración seleccionado.")
        else:
            st.error("El archivo no contiene las columnas necesarias: 'Product Title', 'Term (Month)', 'Tier Min', 'Tier Max' y/o 'MSRP USD'.")
    else:
        st.write("No se pudieron cargar los datos.")

if __name__ == "__main__":
    main()
