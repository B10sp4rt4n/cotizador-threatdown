from PyPDF2 import PdfMerger
import os

def anexar_documentacion(pdf_principal_path, productos, carpeta_base="documentos_productos"):
    """
    Combina el PDF principal de la propuesta con los documentos asociados a cada producto.
    Para cada producto se espera una carpeta con su nombre dentro de `carpeta_base`,
    que contenga uno o más PDFs que serán agregados al final.
    """
    merger = PdfMerger()
    merger.append(pdf_principal_path)

    for producto in productos:
        nombre = producto.get("producto") or producto.get("Producto")
        ruta_carpeta = os.path.join(carpeta_base, nombre)
        if os.path.isdir(ruta_carpeta):
            archivos_pdf = sorted([f for f in os.listdir(ruta_carpeta) if f.lower().endswith(".pdf")])
            for archivo in archivos_pdf:
                path_completo = os.path.join(ruta_carpeta, archivo)
                merger.append(path_completo)

    salida = pdf_principal_path.replace(".pdf", "_completo.pdf")
    merger.write(salida)
    merger.close()
    return salida
