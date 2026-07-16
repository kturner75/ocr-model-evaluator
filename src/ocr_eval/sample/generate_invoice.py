"""Generate invoice sample PDFs (single-page and multi-page) with ground truth."""

from pathlib import Path

from fpdf import FPDF

from ocr_eval.config import DOCUMENTS_DIR
from ocr_eval.sample._write_config import write_document_config, write_expected

INVOICE_EXPECTED = {
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

# Longer line list so items spill onto page 2 (tests multi-page extraction).
MULTIPAGE_LINE_ITEMS = [
    {"description": "Steel Bracket Type A", "quantity": 40, "unit_price": 12.50, "amount": 500.00},
    {"description": "Steel Bracket Type B", "quantity": 25, "unit_price": 18.00, "amount": 450.00},
    {"description": "Hex Bolts M8 (box of 100)", "quantity": 12, "unit_price": 22.00, "amount": 264.00},
    {"description": "Washers Assorted Kit", "quantity": 8, "unit_price": 15.75, "amount": 126.00},
    {"description": "Industrial Lubricant 5L", "quantity": 6, "unit_price": 48.00, "amount": 288.00},
    {"description": "Safety Gloves (pair)", "quantity": 50, "unit_price": 4.25, "amount": 212.50},
    {"description": "Cable Ties 300mm (pack)", "quantity": 30, "unit_price": 6.50, "amount": 195.00},
    {"description": "Wire Loom 10m", "quantity": 15, "unit_price": 9.90, "amount": 148.50},
    {"description": "Junction Box IP65", "quantity": 20, "unit_price": 14.00, "amount": 280.00},
    {"description": "DIN Rail 1m", "quantity": 18, "unit_price": 7.25, "amount": 130.50},
    {"description": "Terminal Block 12-way", "quantity": 24, "unit_price": 11.00, "amount": 264.00},
    {"description": "Contactor 24V Coil", "quantity": 4, "unit_price": 85.00, "amount": 340.00},
    {"description": "Thermal Overload Relay", "quantity": 4, "unit_price": 62.50, "amount": 250.00},
    {"description": "Emergency Stop Button", "quantity": 10, "unit_price": 19.95, "amount": 199.50},
    {"description": "Site Installation Labor", "quantity": 16, "unit_price": 95.00, "amount": 1520.00},
]

_mp_subtotal = sum(i["amount"] for i in MULTIPAGE_LINE_ITEMS)
_mp_tax_rate = 8.25
_mp_tax = round(_mp_subtotal * _mp_tax_rate / 100, 2)

MULTIPAGE_INVOICE_EXPECTED = {
    "invoice_number": "INV-2048",
    "invoice_date": "2024-06-03",
    "due_date": "2024-07-03",
    "vendor_name": "Northwind Industrial Supply",
    "vendor_address": "890 Harbor Blvd, Building C, Seattle, WA 98101",
    "bill_to_name": "Pacific Assembly Co",
    "bill_to_address": "2200 Plant Road, Portland, OR 97201",
    "line_items": MULTIPAGE_LINE_ITEMS,
    "subtotal": _mp_subtotal,
    "tax_rate": _mp_tax_rate,
    "tax_amount": _mp_tax,
    "total": round(_mp_subtotal + _mp_tax, 2),
}

# Backward-compatible name used by tests
EXPECTED_DATA = INVOICE_EXPECTED


def _draw_invoice_header(pdf: FPDF, data: dict) -> None:
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "INVOICE", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, data["vendor_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, data["vendor_address"], new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    pdf.cell(95, 6, f"Invoice Number: {data['invoice_number']}")
    pdf.cell(95, 6, f"Invoice Date: {data['invoice_date']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(95, 6, f"Due Date: {data['due_date']}", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Bill To:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, data["bill_to_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, data["bill_to_address"], new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)


def _draw_line_table_header(pdf: FPDF, col_w: list[int]) -> None:
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[0], 8, "Description", border=1)
    pdf.cell(col_w[1], 8, "Quantity", border=1, align="C")
    pdf.cell(col_w[2], 8, "Unit Price", border=1, align="R")
    pdf.cell(col_w[3], 8, "Amount", border=1, align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)


def _draw_totals(pdf: FPDF, data: dict) -> None:
    pdf.ln(5)
    pdf.cell(110, 7, "")
    pdf.cell(35, 7, "Subtotal:", align="R")
    pdf.cell(35, 7, f"${data['subtotal']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.cell(110, 7, "")
    pdf.cell(35, 7, f"Tax ({data['tax_rate']}%):", align="R")
    pdf.cell(35, 7, f"${data['tax_amount']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(110, 9, "")
    pdf.cell(35, 9, "Total:", align="R")
    pdf.cell(35, 9, f"${data['total']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")


def generate_sample_invoice(output_dir: Path) -> tuple[Path, dict]:
    data = INVOICE_EXPECTED
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    _draw_invoice_header(pdf, data)
    col_w = [80, 30, 35, 35]
    _draw_line_table_header(pdf, col_w)

    for item in data["line_items"]:
        pdf.cell(col_w[0], 7, item["description"], border=1)
        pdf.cell(col_w[1], 7, str(item["quantity"]), border=1, align="C")
        pdf.cell(col_w[2], 7, f"${item['unit_price']:.2f}", border=1, align="R")
        pdf.cell(col_w[3], 7, f"${item['amount']:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    _draw_totals(pdf, data)

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "sample_invoice.pdf"
    pdf.output(str(pdf_path))
    return pdf_path, data


def generate_multipage_invoice(output_dir: Path) -> tuple[Path, dict]:
    """Invoice with enough line items that the table continues on page 2."""
    data = MULTIPAGE_INVOICE_EXPECTED
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    _draw_invoice_header(pdf, data)
    col_w = [80, 30, 35, 35]
    _draw_line_table_header(pdf, col_w)

    for item in data["line_items"]:
        # Keep rows readable; auto page break will spill to page 2
        if pdf.get_y() > 250:
            pdf.add_page()
            _draw_line_table_header(pdf, col_w)
        pdf.cell(col_w[0], 7, item["description"], border=1)
        pdf.cell(col_w[1], 7, str(item["quantity"]), border=1, align="C")
        pdf.cell(col_w[2], 7, f"${item['unit_price']:.2f}", border=1, align="R")
        pdf.cell(col_w[3], 7, f"${item['amount']:.2f}", border=1, align="R", new_x="LMARGIN", new_y="NEXT")

    if pdf.get_y() > 240:
        pdf.add_page()
    _draw_totals(pdf, data)

    # Page footer markers help verify multi-page handling
    page_count = pdf.pages_count
    for page in range(1, page_count + 1):
        pdf.page = page
        pdf.set_y(-15)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(0, 8, f"Page {page} of {page_count}", align="C")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "multipage_invoice.pdf"
    pdf.output(str(pdf_path))
    return pdf_path, data


def write_invoice_configs(pdf_path: Path, expected: dict) -> None:
    write_document_config(
        doc_id="sample_invoice",
        name="Sample Invoice #1001",
        doc_type="invoice",
        pdf_path=pdf_path,
        description="Clean single-page synthetic invoice with known ground truth",
    )
    write_expected(document_id="sample_invoice", schema_id="invoice", expected=expected)


def write_multipage_invoice_configs(pdf_path: Path, expected: dict) -> None:
    write_document_config(
        doc_id="multipage_invoice",
        name="Multi-page Invoice #2048",
        doc_type="invoice",
        pdf_path=pdf_path,
        description="Multi-page industrial invoice; line items span pages",
    )
    write_expected(document_id="multipage_invoice", schema_id="invoice", expected=expected)


def generate_all_sample_data() -> Path:
    """Backward-compatible entry: regenerate full sample suite, return primary invoice path."""
    from ocr_eval.sample.generate_all import generate_all_sample_data as _generate_all

    return _generate_all()
