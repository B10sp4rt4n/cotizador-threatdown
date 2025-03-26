# Cotizador ThreatDown

Cotizador multiproducto con gestión de empresas, contactos y control de acceso. Esta app permite generar propuestas comerciales personalizadas con descuentos, cálculo de márgenes y exportación en PDF o Excel. Incluye funcionalidades tipo CRM y está optimizado para su despliegue en Streamlit Cloud.

---

## 📁 Estructura del Proyecto

```
cotizador_threatdown/
├── backend/
│   ├── database.py              # Conexión y creación de tablas
│   ├── admin/
│   │   ├── empresa_manager.py   # CRUD empresas
│   │   ├── contacto_manager.py  # CRUD contactos
│   │   └── auth.py              # Autenticación y usuarios
│   └── logic/
│       ├── cotizador.py         # Lógica de cotización
│       └── pdf_generator.py
├── frontend/
│   ├── app.py                   # App principal (Streamlit)
│   └── views/
│       ├── login.py
│       ├── cotizacion.py
│       ├── empresas.py
│       └── contactos.py
├── data/
│   ├── precios_threatdown.xlsx
│   └── logos/
│       ├── logo_empresa.png
│       └── logo_threatdown.png
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md
```

---

## 🚀 Instalación local

1. Clona el repositorio:
```bash
git clone https://github.com/tu_usuario/cotizador_threatdown.git
cd cotizador_threatdown
```

2. Instala dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecuta la app:
```bash
streamlit run frontend/app.py
```

---

## ☁️ Despliegue en Streamlit Cloud

Asegúrate de que tu estructura contenga:
- `frontend/app.py` como punto de entrada.
- `.streamlit/config.toml` con la configuración del servidor.

### `.streamlit/config.toml`
```toml
[server]
headless = true
port = 8501
enableCORS = false
```

---

## 🧠 Funcionalidades
- Registro de empresas y contactos asociados
- Cotización multiproducto con descuentos en cascada
- Exportación en PDF y Excel con logotipo personalizado
- Historial de propuestas y comparador
- Control de usuarios (admin / usuario estándar)

---

## 📌 Notas
- Asegúrate de usar `tempfile.gettempdir()` para rutas temporales si estás desplegando en Streamlit Cloud.
- No edites directamente las tablas desde el Excel, usa las vistas administrativas integradas.
