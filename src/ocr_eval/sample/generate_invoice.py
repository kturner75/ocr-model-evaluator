import json
from pathlib import Path

import yaml
from fpdf import FPDF

from ocr_eval.config import CONFIG_DOCUMENTS_DIR, CONFIG_EXPECTED_DIR, DOCUMENTS_DIR

EXPECTED_DATA = {
    "invoice_number": "INV-1001",
    "invoice_date": "2024-01-15",
    "due_date": "2024-02-14",
    "vendor_name": "Acme Corp",
    "vendor_address": "123 Business Ave, Suite 100, San Francisco, CA 94105",
    "bill_to_name": "Widget Industries",
    "bill_to_address": "456 Commerce St, Austin, TX 78701",
    "line_items": [
        {"description": "Widget A", "quantity": 10, "unit_price": 25.00, "amount": 250.00},
        {"description": "Widget B", "quantity": 5, "unit_price": 50.00, "amount": 250.00},
        {"description": "Consulting Services", "quantity": 8, "unit_price": 150.00, "amount": 1200.00},
    ],
    "subtotal": 1700.00,
    "tax_rate": 8.25,
    "tax_amount": 140.25,
    "total": 1840.25,
}


def generate_sample_invoice(output_dir: Path) -> tuple[Path, dict]:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "INVOICE", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, EXPECTED_DATA["vendor_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, EXPECTED_DATA["vendor_address"], new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    pdf.cell(95, 6, f"Invoice Number: {EXPECTED_DATA['invoice_number']}")
    pdf.cell(95, 6, f"Invoice Date: {EXPECTED_DATA['invoice_date']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(95, 6, f"Due Date: {EXPECTED_DATA['due_date']}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, EXPECTED_DATA["bill_to_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, EXPECTED_DATA["bill_to_address"], new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 10)
    col_w = [80, 30, 35, 35]
    pdf.cell(col_w[0], 8, "Description", border=1)
    pdf.cell(col_w[1], 8, "Quantity", border=1, align="C")
    pdf.cell(col_w[2], 8, "Unit Price", border=1, align="R")
    pdf.cell(col_w[3], 8, "Amount", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    for item in EXPECTED_DATA["line_items"]:
        pdf.cell(col_w[0], 7, item["description"], border=1)
        pdf.cell(col_w[1], 7, str(item["quantity"]), border=1, align="C")
        pdf.cell(col_w[2], 7, f"${item['unit_price']:.2f}", border=1, align="R")
        pdf.cell(col_w[3], 7, f"${item['amount']:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)

    pdf.cell(110, 7, "")
    pdf.cell(35, 7, "Subtotal:", align="R")
    pdf.cell(35, 7, f"${EXPECTED_DATA['subtotal']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(110, 7, "")
    pdf.cell(35, 7, f"Tax ({EXPECTED_DATA['tax_rate']}%):", align="R")
    pdf.cell(35, 7, f"${EXPECTED_DATA['tax_amount']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(110, 9, "")
    pdf.cell(35, 9, "Total:", align="R")
    pdf.cell(35, 9, f"${EXPECTED_DATA['total']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "sample_invoice.pdf"
    pdf.output(str(pdf_path))

    return pdf_path, EXPECTED_DATA


def generate_all_sample_data() -> Path:
    pdf_path, expected = generate_sample_invoice(DOCUMENTS_DIR)

    doc_config = {
        "id": "sample_invoice",
        "name": "Sample Invoice #1001",
        "doc_type": "invoice",
        "file_path": str(pdf_path),
        "description": "Programmatically generated invoice for testing",
    }
    with open(CONFIG_DOCUMENTS_DIR / "sample_invoice.yaml", "w") as f:
        yaml.dump(doc_config, f, default_flow_style=False)

    expected_config = {
        "document_id": "sample_invoice",
        "schema_id": "invoice",
        "expected": expected,
    }
    with open(CONFIG_EXPECTED_DIR / "sample_invoice.json", "w") as f:
        json.dump(expected_config, f, indent=2)

    return pdf_path
