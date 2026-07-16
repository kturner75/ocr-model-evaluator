from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RunStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class _MissingType:
    """Sentinel for fields absent from expected or actual JSON during comparison."""
    __slots__ = ()
    def __repr__(self) -> str:
        return "MISSING"

MISSING = _MissingType()


@dataclass
class Document:
    id: str
    name: str
    file_path: str
    doc_type: str
    description: str = ""


@dataclass
class Schema:
    id: str
    name: str
    doc_type: str
    json_schema: dict
    description: str = ""


@dataclass
class Prompt:
    id: str
    name: str
    doc_type: str
    template: str
    description: str = ""


@dataclass
class ModelConfig:
    id: str
    name: str
    provider: str
    model_id: str
    api_base: str | None = None
    parameters: dict = field(default_factory=dict)


@dataclass
class Run:
    id: str
    document_id: str
    schema_id: str
    prompt_id: str
    model_id: str
    status: RunStatus = RunStatus.PENDING
    started_at: str | None = None
    finished_at: str | None = None
    created_at: str | None = None


@dataclass
class FieldResult:
    field_path: str
    expected_value: Any
    actual_value: Any
    match: bool


@dataclass
class Result:
    id: str
    run_id: str
    extracted_json: dict | None = None
    is_valid: bool = False
    validation_errors: list[str] = field(default_factory=list)
    accuracy_score: float = 0.0
    field_results: list[FieldResult] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    wall_clock_seconds: float = 0.0
    error_message: str | None = None
    created_at: str | None = None
