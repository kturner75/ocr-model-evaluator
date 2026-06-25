from unittest.mock import MagicMock, patch

from ocr_eval.models.db import init_db
from ocr_eval.pipeline.extractor import _parse_json, run_batch_extraction
from ocr_eval.pipeline.provider import ProviderResponse


def test_parse_json_plain():
    result = _parse_json('{"key": "value"}')
    assert result == {"key": "value"}


def test_parse_json_code_fence():
    text = 'Here is the result:\n```json\n{"key": "value"}\n```'
    result = _parse_json(text)
    assert result == {"key": "value"}


def test_parse_json_embedded():
    text = 'Some text {"key": "value"} more text'
    result = _parse_json(text)
    assert result == {"key": "value"}


@patch("ocr_eval.pipeline.extractor._provider")
def test_batch_extraction_calls_all_combos(mock_provider):
    init_db()

    mock_response = ProviderResponse(
        content='{"invoice_number": "INV-1001", "invoice_date": "2024-01-15", '
                '"vendor_name": "Acme Corp", "line_items": [], "total": 100}',
        input_tokens=100, output_tokens=50, total_tokens=150,
    )
    mock_provider.extract.return_value = mock_response

    progress_calls = []

    def on_progress(step, total, model_id, doc_id):
        progress_calls.append((step, total, model_id, doc_id))

    results = run_batch_extraction(
        ["sample_invoice"], "invoice", "invoice_extract", ["gpt4o"],
        progress_callback=on_progress,
    )

    assert len(results) == 1
    assert len(progress_calls) == 1
    assert progress_calls[0] == (1, 1, "gpt4o", "sample_invoice")
