from ocr_eval.evaluation.comparator import compare_fields
from ocr_eval.evaluation.scorer import compute_accuracy
from ocr_eval.models.domain import MISSING


def test_exact_match():
    expected = {"invoice_number": "INV-1001", "total": 1840.25}
    actual = {"invoice_number": "INV-1001", "total": 1840.25}
    results = compare_fields(expected, actual)
    assert all(r.match for r in results)
    assert compute_accuracy(results) == 1.0


def test_case_insensitive_match():
    expected = {"vendor_name": "Acme Corp"}
    actual = {"vendor_name": "ACME CORP"}
    results = compare_fields(expected, actual)
    assert results[0].match


def test_numeric_tolerance():
    expected = {"total": 1840.25}
    actual = {"total": 1840.254}
    results = compare_fields(expected, actual)
    assert results[0].match


def test_string_to_number_match():
    expected = {"total": 25.00}
    actual = {"total": "25.00"}
    results = compare_fields(expected, actual)
    assert results[0].match


def test_mismatch():
    expected = {"invoice_number": "INV-1001"}
    actual = {"invoice_number": "INV-1002"}
    results = compare_fields(expected, actual)
    assert not results[0].match
    assert compute_accuracy(results) == 0.0


def test_missing_field():
    expected = {"invoice_number": "INV-1001", "total": 100}
    actual = {"invoice_number": "INV-1001"}
    results = compare_fields(expected, actual)
    assert compute_accuracy(results) == 0.5
    missing_field = [r for r in results if r.field_path == "total"][0]
    assert missing_field.actual_value is MISSING
    assert not missing_field.match


def test_nested_objects():
    expected = {"address": {"street": "123 Main", "city": "SF"}}
    actual = {"address": {"street": "123 Main", "city": "SF"}}
    results = compare_fields(expected, actual)
    assert len(results) == 2
    assert all(r.match for r in results)


def test_array_comparison():
    expected = {"items": [{"desc": "A", "qty": 10}, {"desc": "B", "qty": 5}]}
    actual = {"items": [{"desc": "A", "qty": 10}, {"desc": "B", "qty": 5}]}
    results = compare_fields(expected, actual)
    assert all(r.match for r in results)


def test_array_length_mismatch():
    expected = {"items": [{"desc": "A"}, {"desc": "B"}]}
    actual = {"items": [{"desc": "A"}]}
    results = compare_fields(expected, actual)
    matched = [r for r in results if r.match]
    assert len(matched) == 1


def test_empty_inputs():
    results = compare_fields({}, {})
    assert compute_accuracy(results) == 0.0
