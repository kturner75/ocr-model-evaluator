"""Helpers for writing document config + expected ground truth files."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from ocr_eval.config import CONFIG_DOCUMENTS_DIR, CONFIG_EXPECTED_DIR, PROJECT_ROOT


def relative_doc_path(pdf_path: Path) -> str:
    """Store document paths relative to project root when possible."""
    try:
        return str(pdf_path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(pdf_path)


def write_document_config(
    *,
    doc_id: str,
    name: str,
    doc_type: str,
    pdf_path: Path,
    description: str,
) -> None:
    doc_config = {
        "id": doc_id,
        "name": name,
        "doc_type": doc_type,
        "file_path": relative_doc_path(pdf_path),
        "description": description,
    }
    with open(CONFIG_DOCUMENTS_DIR / f"{doc_id}.yaml", "w") as f:
        yaml.dump(doc_config, f, default_flow_style=False, sort_keys=False)


def write_expected(
    *,
    document_id: str,
    schema_id: str,
    expected: dict,
) -> None:
    payload = {
        "document_id": document_id,
        "schema_id": schema_id,
        "expected": expected,
    }
    with open(CONFIG_EXPECTED_DIR / f"{document_id}.json", "w") as f:
        json.dump(payload, f, indent=2)
