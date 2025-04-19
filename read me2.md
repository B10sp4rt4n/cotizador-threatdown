# 💼 Cotizador ThreatDown con CRM

Aplicación interactiva desarrollada con [Streamlit](https://streamlit.io/) para generar cotizaciones de productos ThreatDown, aplicando distintos tipos de descuentos, calculando márgenes y guardando propuestas en una base de datos CRM local.

---

## 🚀 Funcionalidades principales

### 📊 Cotización personalizada

- Carga dinámica de precios desde un archivo Excel (`precios_threatdown.xlsx`).
- Selección de productos y cantidades según el plazo del servicio (en meses).
- Aplicación de múltiples tipos de descuento:
  - Descuento por ítem
  - Descuento de canal (Channel Disc.)
  - Descuento por Deal Registration

### 💰 Análisis financiero

- Cálculo de:
  - Precio final unitario con descuentos
  - Subtotales por producto
  - Precio total de venta
  - Costo total
  - Utilidad y margen porcentual
- Visualización de resultados con métricas y tablas interactivas.

### 🧾 Gestión de cotizaciones (CRM)

- Guardado de cotizaciones en base de datos SQLite (`crm_cotizaciones.sqlite`).
- Historial de cotizaciones ordenado por fecha.
- Visualización detallada de cotizaciones previas.
- Comparador de propuestas para análisis comercial.

### 📤 Exportación en Excel

- Exportación automática de la cotización en formato `.xlsx`.
- Hoja separada con datos del cliente.
- Fórmulas de totales incorporadas.

---

## 🛠 Tecnologías utilizadas

- **Python 3.12+**
- [Streamlit](https://streamlit.io/) – Interfaz web
- **Pandas** – Manipulación de datos
- **SQLite3** – Almacenamiento de cotizaciones
- **openpyxl / xlsxwriter** – Lectura y escritura de archivos Excel

---

## ✅ Instalación local

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/cotizador-threatdown.git
   cd cotizador-threatdown
