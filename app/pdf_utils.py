
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import List
from fpdf import FPDF

COMPANY_NAME = "E & A"
COMPANY_ADDR = "123 Business St, Business City, 12345"
COMPANY_PHONE = "(123) 456-7890"
COMPANY_EMAIL = "info@tradesmate.com"

TAX_RATE = Decimal("0.10")  # 10 %

DISCLAIMER = (
    "This estimate is valid for 30 days from the date issued. "
    "Prices may vary based on actual time and materials required. "
    "Final invoice may differ from this estimate."
)

class _PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, COMPANY_NAME, ln=True)
        self.set_font("Helvetica", size=10)
        self.multi_cell(0, 5, f"{COMPANY_ADDR}\n{COMPANY_PHONE}\n{COMPANY_EMAIL}")
        self.ln(4)

    def footer(self):
        self.set_y(-30)
        self.set_font("Helvetica", size=8)
        self.multi_cell(0, 4, DISCLAIMER, align="C")

def _add_key_value(pdf: _PDF, key: str, value: str):
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 7, f"{key}:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, value, ln=True)

def build_pdf(payload) -> bytes:
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    today = date.today().isoformat()
    _add_key_value(pdf, "Estimate #", f"EST-{int(date.today().strftime('%s'))}")
    _add_key_value(pdf, "Date", today)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Client Information", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, payload["client_name"])
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Job Details", ln=True)
    pdf.set_font("Helvetica", "", 10)
    _add_key_value(pdf, "Type", payload["job_type"])
    pdf.multi_cell(0, 5, f"Description: {payload['job_description']}")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Itemized Details", ln=True)
    pdf.set_font("Helvetica", "B", 10)
    col_widths = [70, 20, 30, 30]
    headers = ["Description", "Qty", "Unit Price", "Total"]
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, h, border=1, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 10)

    subtotal = Decimal("0")
    for row in payload["items"]:
        line_total = Decimal(row["quantity"]) * Decimal(str(row["unit_price"]))
        subtotal += line_total
        cells = [
            row["description"],
            str(row["quantity"]),
            f"${row['unit_price']:,.2f}",
            f"${line_total:,.2f}",
        ]
        for w, cell in zip(col_widths, cells):
            pdf.cell(w, 7, cell, border=1)
        pdf.ln()

    tax = subtotal * TAX_RATE
    total = subtotal + tax

    pdf.ln(2)
    pdf.cell(0, 6, f"Subtotal: ${subtotal:,.2f}", ln=True, align="R")
    pdf.cell(0, 6, f"Tax ({TAX_RATE * 100:.1f}%): ${tax:,.2f}", ln=True, align="R")
    pdf.cell(0, 6, f"Total: ${total:,.2f}", ln=True, align="R")
    pdf.ln(8)

    if payload.get("notes"):
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Notes & Terms", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, payload["notes"])
        pdf.ln(8)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, "By signing below, you accept this estimate and authorize E & A to proceed.", ln=True)
    pdf.ln(14)
    pdf.cell(60, 6, "Client Signature______________________")
    pdf.cell(0, 6, f"Date {today}", ln=True)

    stream = BytesIO()
    pdf.output(stream)
    return stream.getvalue()
