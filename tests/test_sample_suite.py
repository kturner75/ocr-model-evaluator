from pathlib import Path

from ocr_eval.pipeline.pdf_converter import pdf_to_base64_images
from ocr_eval.sample.generate_all import generate_all_sample_data, list_sample_document_ids
from ocr_eval.sample.generate_invoice import generate_multipage_invoice, generate_sample_invoice
from ocr_eval.sample.generate_purchase_order import generate_sample_purchase_order
from ocr_eval.sample.generate_receipt import generate_sample_receipt
from ocr_eval.stores.document_store import get_document, list_documents
from ocr_eval.stores.expected_store import get_expected
from ocr_eval.stores.prompt_store import list_prompts
from ocr_eval.stores.schema_store import list_schemas
from ocr_eval.pipeline.extractor import resolve_prompt_id, resolve_schema_id


def test_generators_produce_pdfs(tmp_path):
    invoice_path, inv = generate_sample_invoice(tmp_path)
    assert invoice_path.exists()
    assert inv["invoice_number"] == "INV-1001"

    multi_path, multi = generate_multipage_invoice(tmp_path)
    assert multi_path.exists()
    assert len(multi["line_items"]) >= 10

    receipt_path, receipt = generate_sample_receipt(tmp_path)
    assert receipt_path.exists()
    assert receipt["receipt_number"] == "R-88421"

    po_path, po = generate_sample_purchase_order(tmp_path)
    assert po_path.exists()
    assert po["po_number"] == "PO-77801"


def test_multipage_invoice_has_multiple_pages(tmp_path):
    pdf_path, _ = generate_multipage_invoice(tmp_path)
    images = pdf_to_base64_images(pdf_path)
    assert len(images) >= 2


def test_generate_all_writes_configs_and_expected():
    generate_all_sample_data()

    doc_ids = {d.id for d in list_documents()}
    for doc_id in list_sample_document_ids():
        assert doc_id in doc_ids
        doc = get_document(doc_id)
        assert doc is not None
        pdf = Path(doc.file_path)
        if not pdf.is_absolute():
            from ocr_eval.config import PROJECT_ROOT
            pdf = PROJECT_ROOT / pdf
        assert pdf.exists(), f"Missing PDF for {doc_id}: {pdf}"

    schema_types = {s.doc_type for s in list_schemas()}
    prompt_types = {p.doc_type for p in list_prompts()}
    for doc_type in ("invoice", "receipt", "purchase_order"):
        assert doc_type in schema_types
        assert doc_type in prompt_types

    assert get_expected("sample_invoice", "invoice") is not None
    assert get_expected("multipage_invoice", "invoice") is not None
    assert get_expected("sample_receipt", "receipt") is not None
    assert get_expected("sample_purchase_order", "purchase_order") is not None


def test_resolve_schema_and_prompt_by_doc_type():
    generate_all_sample_data()

    assert resolve_schema_id("sample_receipt", preferred_schema_id="invoice") == "receipt"
    assert resolve_schema_id("sample_invoice", preferred_schema_id="invoice") == "invoice"
    assert resolve_prompt_id("sample_purchase_order", preferred_prompt_id="invoice_extract") == (
        "purchase_order_extract"
    )
    assert resolve_prompt_id("sample_invoice", preferred_prompt_id="invoice_extract") == (
        "invoice_extract"
    )
