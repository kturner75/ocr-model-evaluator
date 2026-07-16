"""Generate a retail-style receipt PDF with ground truth."""

from pathlib import Path

from fpdf import FPDF

from ocr_eval.sample._write_config import write_document_config, write_expected

RECEIPT_EXPECTED = {
    "merchant_name": "Corner Market Grocery",
    "merchant_address": "77 Pine Street, Denver, CO 80202",
    "receipt_number": "R-88421",
    "transaction_date": "2024-09-12",
    "transaction_time": "14:37",
    "cashier_id": "C12",
    "payment_method": "Visa ****4242",
    "line_items": [
        {"description": "Organic Bananas 1lb", "quantity": 2, "unit_price": 0.69, "amount": 1.38},
        {"description": "Whole Milk 1gal", "quantity": 1, "unit_price": 3.99, "amount": 3.99},
        {"description": "Sourdough Loaf", "quantity": 1, "unit_price": 4.50, "amount": 4.50},
        {"description": "Large Eggs Dozen", "quantity": 1, "unit_price": 5.29, "amount": 5.29},
        {"description": "Ground Coffee 12oz", "quantity": 1, "unit_price": 9.99, "amount": 9.99},
        {"description": "Paper Towels 6pk", "quantity": 1, "unit_price": 12.49, "amount": 12.49},
    ],
    "subtotal": 37.64,
    "tax_rate": 8.81,
    "tax_amount": 3.32,
    "total": 40.96,
}


def generate_sample_receipt(output_dir: Path) -> tuple[Path, dict]:
    data = RECEIPT_EXPECTED
    # Narrow page mimics thermal receipt proportions while staying A4-compatible for converters
    pdf = FPDF(format=(80, 200))  # mm, receipt-ish width
    pdf.set_margins(5, 5, 5)
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=8)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 6, data["merchant_name"], new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(0, 4, data["merchant_address"], new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(3)
    pdf.cell(0, 4, f"Receipt #: {data['receipt_number']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        4,
        f"Date: {data['transaction_date']}  Time: {data['transaction_time']}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.cell(0, 4, f"Cashier: {data['cashier_id']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.cell(0, 3, "-" * 42, new_x="LMARGIN", new_y="NEXT")

    for item in data["line_items"]:
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(0, 4, item["description"], new_x="LMARGIN", new_y="NEXT")
        detail = f"  {item['quantity']} x ${item['unit_price']:.2f}"
        pdf.cell(40, 4, detail)
        pdf.cell(0, 4, f"${item['amount']:.2f}", new_x="LMARGIN", new_y="NEXT", align="R")

    pdf.cell(0, 3, "-" * 42, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(40, 4, "Subtotal")
    pdf.cell(0, 4, f"${data['subtotal']:.2f}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.cell(40, 4, f"Tax ({data['tax_rate']}%)")
    pdf.cell(0, 4, f"${data['tax_amount']:.2f}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(40, 5, "TOTAL")
    pdf.cell(0, 5, f"${data['total']:.2f}", new_x="LMARGIN", new_y="NEXT", align="R")
    pdf.set_font("Helvetica", "", 7)
    pdf.ln(2)
    pdf.cell(0, 4, f"Paid: {data['payment_method']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 4, "Thank you for shopping!", new_x="LMARGIN", new_y="NEXT", align="C")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "sample_receipt.pdf"
    pdf.output(str(pdf_path))
    return pdf_path, data


def write_receipt_configs(pdf_path: Path, expected: dict) -> None:
    write_document_config(
        doc_id="sample_receipt",
        name="Sample Grocery Receipt",
        doc_type="receipt",
        pdf_path=pdf_path,
        description="Narrow retail receipt layout with payment method and tax",
    )
    write_expected(document_id="sample_receipt", schema_id="receipt", expected=expected)
