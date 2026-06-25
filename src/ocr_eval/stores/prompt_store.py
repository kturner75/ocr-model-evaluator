import json

import yaml
from ocr_eval.config import CONFIG_PROMPTS_DIR
from ocr_eval.models.domain import Prompt


def list_prompts() -> list[Prompt]:
    prompts = []
    for f in sorted(CONFIG_PROMPTS_DIR.glob("*.yaml")):
        with open(f) as fh:
            data = yaml.safe_load(fh)
        prompts.append(Prompt(
            id=data["id"], name=data["name"], doc_type=data["doc_type"],
            template=data["template"], description=data.get("description", ""),
        ))
    return prompts


def get_prompt(prompt_id: str) -> Prompt | None:
    for p in list_prompts():
        if p.id == prompt_id:
            return p
    return None


def render_prompt(prompt_id: str, schema_json: dict) -> str:
    prompt = get_prompt(prompt_id)
    if not prompt:
        raise ValueError(f"Prompt not found: {prompt_id}")
    return prompt.template.replace("{schema_json}", json.dumps(schema_json, indent=2))
