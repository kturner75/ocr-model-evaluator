from ocr_eval.evaluation.scorer import compute_accuracy, generate_diff_report
from ocr_eval.models.domain import FieldResult


def test_compute_accuracy_all_match():
    results = [
        FieldResult("a", "x", "x", True),
        FieldResult("b", "y", "y", True),
    ]
    assert compute_accuracy(results) == 1.0


def test_compute_accuracy_partial():
    results = [
        FieldResult("a", "x", "x", True),
        FieldResult("b", "y", "z", False),
    ]
    assert compute_accuracy(results) == 0.5


def test_compute_accuracy_empty():
    assert compute_accuracy([]) == 0.0


def test_generate_diff_report():
    results = [
        FieldResult("invoice_number", "INV-1001", "INV-1001", True),
        FieldResult("total", 100.0, 200.0, False),
    ]
    report = generate_diff_report(results)
    assert "Accuracy: 50.0%" in report
    assert "[OK] invoice_number" in report
    assert "[XX] total" in report
