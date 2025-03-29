import datetime

# Pedir entrada al usuario
cambio = input("🛠️ Describe brevemente el cambio realizado: ").strip()
if not cambio:
    print("⚠️ No se ingresó ninguna descripción. Cancelado.")
    exit()

# Obtener fecha actual
fecha = datetime.datetime.now().strftime("%Y-%m-%d")

# Línea a escribir
linea = f"- {cambio}\n"

# Archivo de changelog
ruta_changelog = "CHANGELOG.md"

try:
    with open(ruta_changelog, "r", encoding="utf-8") as f:
        contenido = f.readlines()
except FileNotFoundError:
    contenido = []

# Buscar si ya hay sección con la fecha actual
indice_fecha = None
for i, linea_existente in enumerate(contenido):
    if fecha in linea_existente:
        indice_fecha = i
        break

if indice_fecha is not None:
    # Insertar el cambio debajo de la fecha
    contenido.insert(indice_fecha + 1, linea)
else:
    # Agregar nueva sección
    contenido.insert(0, f"\n### {fecha}\n")
    contenido.insert(1, linea)

# Guardar cambios
with open(ruta_changelog, "w", encoding="utf-8") as f:
    f.writelines(contenido)

print(f"✅ Cambio registrado en {ruta_changelog}")
