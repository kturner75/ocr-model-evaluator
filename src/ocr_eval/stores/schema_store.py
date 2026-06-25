import json
from ocr_eval.config import CONFIG_SCHEMAS_DIR
from ocr_eval.models.domain import Schema


def list_schemas() -> list[Schema]:
    schemas = []
    for f in sorted(CONFIG_SCHEMAS_DIR.glob("*.json")):
        with open(f) as fh:
            data = json.load(fh)
        schemas.append(Schema(
            id=data["id"], name=data["name"], doc_type=data["doc_type"],
            json_schema=data["json_schema"], description=data.get("description", ""),
        ))
    return schemas


def get_schema(schema_id: str) -> Schema | None:
    for s in list_schemas():
        if s.id == schema_id:
            return s
    return None
