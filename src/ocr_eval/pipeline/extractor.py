import json
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from ocr_eval.evaluation.comparator import compare_fields
from ocr_eval.evaluation.scorer import compute_accuracy
from ocr_eval.evaluation.validator import validate_extraction
from ocr_eval.models.db import create_run, save_result, update_run
from ocr_eval.models.domain import Result, RunStatus
from ocr_eval.pipeline.pdf_converter import pdf_to_base64_images
from ocr_eval.pipeline.provider import LiteLLMProvider
from ocr_eval.stores.document_store import get_document
from ocr_eval.stores.expected_store import get_expected
from ocr_eval.stores.model_store import get_model
from ocr_eval.stores.prompt_store import render_prompt
from ocr_eval.stores.schema_store import get_schema

_provider = LiteLLMProvider()


def _parse_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        return json.loads(text[start : end + 1])

    raise ValueError(f"Could not parse JSON from response: {text[:200]}")


def run_extraction(
    document_id: str,
    schema_id: str,
    prompt_id: str,
    model_id: str,
) -> Result:
    run = create_run(document_id, schema_id, prompt_id, model_id)
    now = datetime.now(timezone.utc).isoformat()
    update_run(run.id, RunStatus.RUNNING, started_at=now)

    try:
        document = get_document(document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        schema = get_schema(schema_id)
        if not schema:
            raise ValueError(f"Schema not found: {schema_id}")

        model_config = get_model(model_id)
        if not model_config:
            raise ValueError(f"Model not found: {model_id}")

        rendered_prompt = render_prompt(prompt_id, schema.json_schema)

        pdf_path = Path(document.file_path)
        if not pdf_path.is_absolute():
            from ocr_eval.config import PROJECT_ROOT
            pdf_path = PROJECT_ROOT / pdf_path

        base64_images = pdf_to_base64_images(pdf_path)

        content: list[dict] = [{"type": "text", "text": rendered_prompt}]
        for img_uri in base64_images:
            content.append({"type": "image_url", "image_url": {"url": img_uri, "detail": "high"}})

        messages = [{"role": "user", "content": content}]

        start_time = time.perf_counter()
        response = _provider.extract(messages, model_config)
        wall_clock = time.perf_counter() - start_time

        extracted_json = _parse_json(response.content)

        is_valid, validation_errors = validate_extraction(extracted_json, schema.json_schema)

        expected = get_expected(document_id, schema_id)
        field_results = []
        accuracy_score = 0.0
        if expected:
            field_results = compare_fields(expected, extracted_json)
            accuracy_score = compute_accuracy(field_results)

        result = Result(
            id=str(uuid.uuid4()),
            run_id=run.id,
            extracted_json=extracted_json,
            is_valid=is_valid,
            validation_errors=validation_errors,
            accuracy_score=accuracy_score,
            field_results=field_results,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            total_tokens=response.total_tokens,
            wall_clock_seconds=wall_clock,
        )

        save_result(result)
        update_run(run.id, RunStatus.COMPLETED, finished_at=datetime.now(timezone.utc).isoformat())
        return result

    except Exception as e:
        error_result = Result(
            id=str(uuid.uuid4()),
            run_id=run.id,
            error_message=str(e),
        )
        save_result(error_result)
        update_run(run.id, RunStatus.FAILED, finished_at=datetime.now(timezone.utc).isoformat())
        return error_result
