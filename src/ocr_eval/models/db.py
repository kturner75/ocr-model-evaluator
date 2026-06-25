import json
import sqlite3
import uuid
from datetime import datetime, timezone

from ocr_eval.config import DB_PATH
from ocr_eval.models.domain import FieldResult, Result, Run, RunStatus

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    schema_id TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    started_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL UNIQUE REFERENCES runs(id),
    extracted_json TEXT,
    is_valid INTEGER,
    validation_errors TEXT,
    accuracy_score REAL,
    field_results TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    wall_clock_seconds REAL,
    error_message TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _get_conn() as conn:
        conn.executescript(_CREATE_TABLES)


def create_run(document_id: str, schema_id: str, prompt_id: str, model_id: str) -> Run:
    run = Run(
        id=str(uuid.uuid4()),
        document_id=document_id,
        schema_id=schema_id,
        prompt_id=prompt_id,
        model_id=model_id,
        status=RunStatus.PENDING,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO runs (id, document_id, schema_id, prompt_id, model_id, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run.id, run.document_id, run.schema_id, run.prompt_id, run.model_id, run.status.value, run.created_at),
        )
    return run


def update_run(run_id: str, status: RunStatus, started_at: str | None = None, finished_at: str | None = None) -> None:
    with _get_conn() as conn:
        parts = ["status = ?"]
        params: list = [status.value]
        if started_at:
            parts.append("started_at = ?")
            params.append(started_at)
        if finished_at:
            parts.append("finished_at = ?")
            params.append(finished_at)
        params.append(run_id)
        conn.execute(f"UPDATE runs SET {', '.join(parts)} WHERE id = ?", params)


def save_result(result: Result) -> None:
    field_results_json = json.dumps(
        [{"field_path": fr.field_path, "expected_value": fr.expected_value, "actual_value": fr.actual_value, "match": fr.match}
         for fr in result.field_results]
    )
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO results (id, run_id, extracted_json, is_valid, validation_errors, "
            "accuracy_score, field_results, input_tokens, output_tokens, total_tokens, "
            "wall_clock_seconds, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                result.id, result.run_id,
                json.dumps(result.extracted_json) if result.extracted_json else None,
                int(result.is_valid), json.dumps(result.validation_errors),
                result.accuracy_score, field_results_json,
                result.input_tokens, result.output_tokens, result.total_tokens,
                result.wall_clock_seconds, result.error_message,
            ),
        )


def _row_to_run(row: sqlite3.Row) -> Run:
    return Run(
        id=row["id"], document_id=row["document_id"], schema_id=row["schema_id"],
        prompt_id=row["prompt_id"], model_id=row["model_id"],
        status=RunStatus(row["status"]), started_at=row["started_at"],
        finished_at=row["finished_at"], created_at=row["created_at"],
    )


def _row_to_result(row: sqlite3.Row) -> Result:
    field_results_raw = json.loads(row["field_results"]) if row["field_results"] else []
    return Result(
        id=row["id"], run_id=row["run_id"],
        extracted_json=json.loads(row["extracted_json"]) if row["extracted_json"] else None,
        is_valid=bool(row["is_valid"]),
        validation_errors=json.loads(row["validation_errors"]) if row["validation_errors"] else [],
        accuracy_score=row["accuracy_score"] or 0.0,
        field_results=[FieldResult(**fr) for fr in field_results_raw],
        input_tokens=row["input_tokens"] or 0, output_tokens=row["output_tokens"] or 0,
        total_tokens=row["total_tokens"] or 0, wall_clock_seconds=row["wall_clock_seconds"] or 0.0,
        error_message=row["error_message"], created_at=row["created_at"],
    )


def get_run(run_id: str) -> Run | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
    return _row_to_run(row) if row else None


def get_result_by_run(run_id: str) -> Result | None:
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM results WHERE run_id = ?", (run_id,)).fetchone()
    return _row_to_result(row) if row else None


def list_runs(limit: int = 50) -> list[Run]:
    with _get_conn() as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    return [_row_to_run(r) for r in rows]


def get_latest_results_by_model(model_ids: list[str], document_ids: list[str] | None = None) -> list[dict]:
    with _get_conn() as conn:
        placeholders = ",".join("?" * len(model_ids))
        query = f"""
            SELECT r.*, res.*,
                   r.model_id as r_model_id, r.document_id as r_document_id
            FROM runs r
            JOIN results res ON res.run_id = r.id
            WHERE r.model_id IN ({placeholders})
              AND r.status = 'completed'
        """
        params: list = list(model_ids)

        if document_ids:
            doc_placeholders = ",".join("?" * len(document_ids))
            query += f" AND r.document_id IN ({doc_placeholders})"
            params.extend(document_ids)

        query += """
            AND r.created_at = (
                SELECT MAX(r2.created_at) FROM runs r2
                WHERE r2.model_id = r.model_id
                  AND r2.document_id = r.document_id
                  AND r2.status = 'completed'
            )
            ORDER BY r.model_id, r.document_id
        """
        rows = conn.execute(query, params).fetchall()

    results = []
    for row in rows:
        results.append({
            "model_id": row["r_model_id"],
            "document_id": row["r_document_id"],
            "accuracy_score": row["accuracy_score"] or 0.0,
            "wall_clock_seconds": row["wall_clock_seconds"] or 0.0,
            "input_tokens": row["input_tokens"] or 0,
            "output_tokens": row["output_tokens"] or 0,
            "total_tokens": row["total_tokens"] or 0,
            "is_valid": bool(row["is_valid"]),
            "error_message": row["error_message"],
            "extracted_json": json.loads(row["extracted_json"]) if row["extracted_json"] else None,
            "created_at": row["created_at"],
        })
    return results


def get_distinct_model_ids() -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT model_id FROM runs WHERE status = 'completed' ORDER BY model_id"
        ).fetchall()
    return [r["model_id"] for r in rows]


def get_distinct_document_ids() -> list[str]:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT document_id FROM runs WHERE status = 'completed' ORDER BY document_id"
        ).fetchall()
    return [r["document_id"] for r in rows]


def export_results(run_ids: list[str] | None = None) -> list[dict]:
    with _get_conn() as conn:
        if run_ids:
            placeholders = ",".join("?" * len(run_ids))
            query = f"""
                SELECT r.model_id, r.document_id, r.schema_id, r.prompt_id,
                       r.status, r.created_at as run_created_at,
                       res.accuracy_score, res.wall_clock_seconds,
                       res.input_tokens, res.output_tokens, res.total_tokens,
                       res.is_valid, res.error_message, res.extracted_json
                FROM runs r LEFT JOIN results res ON res.run_id = r.id
                WHERE r.id IN ({placeholders})
                ORDER BY r.created_at DESC
            """
            rows = conn.execute(query, run_ids).fetchall()
        else:
            rows = conn.execute("""
                SELECT r.model_id, r.document_id, r.schema_id, r.prompt_id,
                       r.status, r.created_at as run_created_at,
                       res.accuracy_score, res.wall_clock_seconds,
                       res.input_tokens, res.output_tokens, res.total_tokens,
                       res.is_valid, res.error_message, res.extracted_json
                FROM runs r LEFT JOIN results res ON res.run_id = r.id
                ORDER BY r.created_at DESC
            """).fetchall()

    return [dict(row) for row in rows]
