"""Regenerate the full sample document suite with configs and ground truth."""

from pathlib import Path

from ocr_eval.config import DOCUMENTS_DIR
from ocr_eval.sample.generate_invoice import (
    generate_multipage_invoice,
    generate_sample_invoice,
    write_invoice_configs,
    write_multipage_invoice_configs,
)
from ocr_eval.sample.generate_purchase_order import (
    generate_sample_purchase_order,
    write_purchase_order_configs,
)
from ocr_eval.sample.generate_receipt import generate_sample_receipt, write_receipt_configs


def generate_all_sample_data() -> Path:
    """
    Generate all sample PDFs and write document/expected configs.

    Returns path to the primary sample invoice PDF (for UI messaging).
    """
    invoice_path, invoice_expected = generate_sample_invoice(DOCUMENTS_DIR)
    write_invoice_configs(invoice_path, invoice_expected)

    multipage_path, multipage_expected = generate_multipage_invoice(DOCUMENTS_DIR)
    write_multipage_invoice_configs(multipage_path, multipage_expected)

    receipt_path, receipt_expected = generate_sample_receipt(DOCUMENTS_DIR)
    write_receipt_configs(receipt_path, receipt_expected)

    po_path, po_expected = generate_sample_purchase_order(DOCUMENTS_DIR)
    write_purchase_order_configs(po_path, po_expected)

    return invoice_path


def list_sample_document_ids() -> list[str]:
    return [
        "sample_invoice",
        "multipage_invoice",
        "sample_receipt",
        "sample_purchase_order",
    ]
