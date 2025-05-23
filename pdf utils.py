# pdf_utils.py
from fpdf import FPDF

class CotizacionPDFConLogo(FPDF):
    def __init__(self, logo_path="logo_empresa.png"):
        super().__init__()
        self.logo_path = logo_path

    def header(self):
        self.image(self.logo_path, x=10, y=8, w=50)
        self.set_font("Helvetica", "B", 16)
        self.set_xy(70, 12)
        self.cell(0, 10, "Cotización de Servicios", ln=True, align="L")
        self.ln(20)

    def encabezado_cliente(self, datos):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, f"Cliente: {datos['cliente']}", ln=True)
        self.cell(0, 8, f"Contacto: {datos['contacto']}", ln=True)
        self.cell(0, 8, f"Propuesta: {datos['propuesta']}", ln=True)
        self.cell(0, 8, f"Fecha: {datos['fecha']}", ln=True)
        self.cell(0, 8, f"Responsable: {datos['responsable']}", ln=True)
        self.ln(5)

    def tabla_productos(self, productos):
        self.set_font("Helvetica", "B", 10)
        self.cell(60, 8, "Producto", 1)
        self.cell(20, 8, "Cantidad", 1, align="C")
        self.cell(30, 8, "P. Unitario", 1, align="R")
        self.cell(30, 8, "Descuento %", 1, align="R")
        self.cell(40, 8, "Total", 1, ln=True, align="R")

        self.set_font("Helvetica", "", 10)
        for p in productos:
            self.cell(60, 8, str(p["producto"]), 1)
            self.cell(20, 8, str(p["cantidad"]), 1, align="C")
            self.cell(30, 8, f"${p['precio_unitario']:,.2f}", 1, align="R")
            self.cell(30, 8, f"{p['descuento_aplicado']}%", 1, align="R")
            self.cell(40, 8, f"${p['precio_total']:,.2f}", 1, ln=True, align="R")
        self.ln(5)

    def totales(self, total_venta):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, f"Total de la propuesta: ${total_venta:,.2f}", ln=True, align="R")
        self.ln(10)

    def condiciones(self, vigencia, condiciones):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 6, f"Vigencia de la propuesta: {vigencia}\n")
        self.multi_cell(0, 6, condiciones)
        self.ln(10)

    def firma(self, responsable):
        self.set_font("Helvetica", "", 10)
        self.cell(0, 8, "Atentamente:", ln=True)
        self.cell(0, 8, responsable, ln=True)
        self.cell(0, 8, "SYNAPPSSYS", ln=True)
