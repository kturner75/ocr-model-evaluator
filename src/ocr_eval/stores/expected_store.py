import json
from ocr_eval.config import CONFIG_EXPECTED_DIR


def get_expected(document_id: str, schema_id: str) -> dict | None:
    for f in sorted(CONFIG_EXPECTED_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
        if data.get("document_id") == document_id and data.get("schema_id") == schema_id:
            return data["expected"]
    return None


def list_expected() -> list[dict]:
    results = []
    for f in sorted(CONFIG_EXPECTED_DIR.glob("*.json")):
        with open(f) as fh:
            results.append(json.load(fh))
    return results
