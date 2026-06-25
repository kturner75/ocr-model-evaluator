import uuid

from ocr_eval.models.db import (
    create_run,
    export_results,
    get_distinct_document_ids,
    get_distinct_model_ids,
    get_latest_results_by_model,
    get_result_by_run,
    get_run,
    init_db,
    list_runs,
    save_result,
    update_run,
)
from ocr_eval.models.domain import FieldResult, Result, RunStatus


def _setup():
    init_db()


def test_create_and_get_run():
    _setup()
    run = create_run("doc1", "schema1", "prompt1", "model1")
    assert run.status == RunStatus.PENDING
    fetched = get_run(run.id)
    assert fetched is not None
    assert fetched.document_id == "doc1"


def test_update_run_status():
    _setup()
    run = create_run("doc1", "schema1", "prompt1", "model1")
    update_run(run.id, RunStatus.COMPLETED, finished_at="2024-01-01T00:00:00")
    fetched = get_run(run.id)
    assert fetched.status == RunStatus.COMPLETED
    assert fetched.finished_at == "2024-01-01T00:00:00"


def test_save_and_get_result():
    _setup()
    run = create_run("doc1", "schema1", "prompt1", "model1")
    update_run(run.id, RunStatus.COMPLETED)
    result = Result(
        id=str(uuid.uuid4()), run_id=run.id,
        extracted_json={"invoice_number": "INV-1"}, is_valid=True,
        accuracy_score=0.85,
        field_results=[FieldResult("invoice_number", "INV-1", "INV-1", True)],
        input_tokens=100, output_tokens=50, total_tokens=150,
        wall_clock_seconds=1.5,
    )
    save_result(result)
    fetched = get_result_by_run(run.id)
    assert fetched is not None
    assert fetched.accuracy_score == 0.85
    assert fetched.total_tokens == 150
    assert len(fetched.field_results) == 1


def test_list_runs():
    _setup()
    create_run("doc1", "schema1", "prompt1", "modelA")
    create_run("doc2", "schema1", "prompt1", "modelB")
    runs = list_runs()
    assert len(runs) >= 2


def test_get_distinct_ids():
    _setup()
    run1 = create_run("docX", "schema1", "prompt1", "modelX")
    update_run(run1.id, RunStatus.COMPLETED)
    save_result(Result(id=str(uuid.uuid4()), run_id=run1.id, accuracy_score=1.0))

    model_ids = get_distinct_model_ids()
    doc_ids = get_distinct_document_ids()
    assert "modelX" in model_ids
    assert "docX" in doc_ids


def test_get_latest_results_by_model():
    _setup()
    run = create_run("docY", "schema1", "prompt1", "modelY")
    update_run(run.id, RunStatus.COMPLETED)
    save_result(Result(
        id=str(uuid.uuid4()), run_id=run.id,
        accuracy_score=0.9, wall_clock_seconds=2.0,
        input_tokens=200, output_tokens=100, total_tokens=300,
    ))

    data = get_latest_results_by_model(["modelY"], ["docY"])
    assert len(data) >= 1
    match = [d for d in data if d["model_id"] == "modelY" and d["document_id"] == "docY"]
    assert len(match) == 1
    assert match[0]["accuracy_score"] == 0.9


def test_export_results():
    _setup()
    exported = export_results()
    assert isinstance(exported, list)
    if exported:
        assert "model_id" in exported[0]
        assert "accuracy_score" in exported[0]
