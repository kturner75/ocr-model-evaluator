"""Generate a purchase order PDF with ground truth."""

from pathlib import Path

from fpdf import FPDF

from ocr_eval.sample._write_config import write_document_config, write_expected

PO_EXPECTED = {
    "po_number": "PO-77801",
    "po_date": "2024-03-18",
    "buyer_name": "Lakeside Manufacturing LLC",
    "buyer_address": "1500 Industrial Parkway, Milwaukee, WI 53201",
    "vendor_name": "Summit Components Inc",
    "vendor_address": "42 Ridge Road, Chicago, IL 60601",
    "ship_to_name": "Lakeside Dock 3 Receiving",
    "ship_to_address": "1500 Industrial Parkway, Gate B, Milwaukee, WI 53201",
    "requested_delivery_date": "2024-04-01",
    "payment_terms": "Net 30",
    "line_items": [
        {
            "item_number": "SC-100",
            "description": "Servo Motor 2kW",
            "quantity": 3,
            "unit_price": 420.00,
            "amount": 1260.00,
        },
        {
            "item_number": "SC-214",
            "description": "Encoder Cable 5m",
            "quantity": 6,
            "unit_price": 48.50,
            "amount": 291.00,
        },
        {
            "item_number": "SC-330",
            "description": "Mounting Flange Kit",
            "quantity": 3,
            "unit_price": 75.00,
            "amount": 225.00,
        },
        {
            "item_number": "SC-441",
            "description": "Drive Firmware License",
            "quantity": 1,
            "unit_price": 199.00,
            "amount": 199.00,
        },
    ],
    "subtotal": 1975.00,
    "tax_amount": 0.00,
    "shipping_amount": 45.00,
    "total": 2020.00,
}


def generate_sample_purchase_order(output_dir: Path) -> tuple[Path, dict]:
    data = PO_EXPECTED
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 12, "PURCHASE ORDER", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(95, 6, f"PO Number: {data['po_number']}")
    pdf.cell(95, 6, f"Date: {data['po_date']}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 6, f"Payment Terms: {data['payment_terms']}")
    pdf.cell(
        95,
        6,
        f"Requested Delivery: {data['requested_delivery_date']}",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(8)

    # Two-column buyer / vendor
    y0 = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(95, 6, "Buyer:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(95, 5, data["buyer_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(90, 5, data["buyer_address"])
    y_left = pdf.get_y()

    pdf.set_xy(110, y0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(90, 6, "Vendor:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(110)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(90, 5, data["vendor_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(110)
    pdf.multi_cell(90, 5, data["vendor_address"])
    y_right = pdf.get_y()

    pdf.set_y(max(y_left, y_right) + 6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Ship To:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, data["ship_to_name"], new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, data["ship_to_address"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    col_w = [28, 72, 25, 30, 30]
    pdf.set_font("Helvetica", "B", 9)
    headers = ["Item #", "Description", "Qty", "Unit Price", "Amount"]
    for i, h in enumerate(headers):
        align = "C" if i == 2 else ("R" if i >= 3 else "L")
        last = i == len(headers) - 1
        pdf.cell(
            col_w[i],
            7,
            h,
            border=1,
            align=align,
            new_x="LMARGIN" if last else "RIGHT",
            new_y="NEXT" if last else "TOP",
        )

    pdf.set_font("Helvetica", "", 9)
    for item in data["line_items"]:
        pdf.cell(col_w[0], 7, item["item_number"], border=1)
        pdf.cell(col_w[1], 7, item["description"], border=1)
        pdf.cell(col_w[2], 7, str(item["quantity"]), border=1, align="C")
        pdf.cell(col_w[3], 7, f"${item['unit_price']:.2f}", border=1, align="R")
        pdf.cell(
            col_w[4],
            7,
            f"${item['amount']:.2f}",
            border=1,
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    pdf.ln(6)
    pdf.cell(125, 6, "")
    pdf.cell(30, 6, "Subtotal:", align="R")
    pdf.cell(30, 6, f"${data['subtotal']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(125, 6, "")
    pdf.cell(30, 6, "Tax:", align="R")
    pdf.cell(30, 6, f"${data['tax_amount']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(125, 6, "")
    pdf.cell(30, 6, "Shipping:", align="R")
    pdf.cell(30, 6, f"${data['shipping_amount']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(125, 8, "")
    pdf.cell(30, 8, "Total:", align="R")
    pdf.cell(30, 8, f"${data['total']:.2f}", align="R", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)
    pdf.set_font("Helvetica", "I", 9)
    pdf.cell(0, 5, "Authorized Buyer Signature: ______________________", new_x="LMARGIN", new_y="NEXT")

    output_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = output_dir / "sample_purchase_order.pdf"
    pdf.output(str(pdf_path))
    return pdf_path, data


def write_purchase_order_configs(pdf_path: Path, expected: dict) -> None:
    write_document_config(
        doc_id="sample_purchase_order",
        name="Sample Purchase Order #77801",
        doc_type="purchase_order",
        pdf_path=pdf_path,
        description="Purchase order with ship-to, payment terms, and item numbers",
    )
    write_expected(
        document_id="sample_purchase_order",
        schema_id="purchase_order",
        expected=expected,
    )
