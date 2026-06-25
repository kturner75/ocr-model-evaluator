# OCR Model Evaluator

## What this project does
Evaluates LLM/OCR models for document extraction by running them against sample documents and comparing accuracy, speed, and token usage via a Streamlit dashboard.

## Tech stack
- Python 3.11+, Streamlit, LiteLLM, PyMuPDF, fpdf2, SQLite, Plotly, jsonschema

## How to run
```bash
pip install -e ".[dev]"     # Install dependencies
streamlit run app.py        # Start dashboard at localhost:8501
pytest                      # Run tests
```

## Architecture
- **Config files** (YAML/JSON in `config/`) define documents, schemas, prompts, models, and expected outputs — these are version-controlled and human-editable
- **SQLite** (`data/results.db`) stores run results only — runtime data
- **LiteLLM** provides a unified API for all model providers; the `Provider` Protocol in `pipeline/provider.py` is the adapter boundary for non-LiteLLM providers
- **Extraction flow**: PDF → base64 images (PyMuPDF) → LLM via LiteLLM → parse JSON → validate against schema → compare against expected output → score accuracy → save to DB

## Key patterns
- Model configs use LiteLLM model strings. For Anthropic: `anthropic/claude-sonnet-4-6` (alias format, not dated IDs)
- The assertion engine does field-level exact match with case-insensitive strings and numeric tolerance (0.01)
- `run_extraction()` is the single-doc orchestrator; `run_batch_extraction()` runs the cartesian product of docs × models

## Testing
- Tests in `tests/` — run with `pytest`
- Tests mock the LLM provider to avoid API calls
- Sample invoice PDF is generated programmatically with known values for deterministic testing
