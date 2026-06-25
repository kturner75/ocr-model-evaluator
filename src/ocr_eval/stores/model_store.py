import yaml
from ocr_eval.config import CONFIG_MODELS_DIR
from ocr_eval.models.domain import ModelConfig


def list_models() -> list[ModelConfig]:
    models = []
    for f in sorted(CONFIG_MODELS_DIR.glob("*.yaml")):
        with open(f) as fh:
            data = yaml.safe_load(fh)
        models.append(ModelConfig(
            id=data["id"], name=data["name"], provider=data["provider"],
            model_id=data["model_id"], api_base=data.get("api_base"),
            parameters=data.get("parameters", {}),
        ))
    return models


def get_model(model_id: str) -> ModelConfig | None:
    for m in list_models():
        if m.id == model_id:
            return m
    return None
