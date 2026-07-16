# OCR Model Evaluator

Evaluate LLM and OCR models for document extraction by running them against a shared suite of sample documents and comparing accuracy, speed, and token usage.

## Features

- **Multi-model comparison** — test cloud models (GPT-4o, Claude, Mistral) and local models (Ollama) through a unified LiteLLM interface
- **Structured extraction** — extract data from PDFs/images into JSON conforming to a defined schema
- **Assertion framework** — field-level exact match comparison against expected output with accuracy scoring
- **Batch evaluation** — run any combination of documents × models in one go
- **Interactive dashboard** — Streamlit UI with Plotly charts for accuracy, speed, and token usage comparison
- **Export** — download results as CSV or JSON

## Quick Start

### Prerequisites

- Python 3.11+
- An API key for at least one supported model (e.g., OpenAI)

### Install

```bash
pip install -e ".[dev]"
```

### Configure

Copy the example env file and add your API key(s):

```bash
cp .env.example .env
# Edit .env with your keys:
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
```

### Run

```bash
streamlit run app.py
```

On first launch, click **Generate Sample Data** in the sidebar to create the sample document suite (invoice, multi-page invoice, receipt, purchase order) with ground truth assertions. Then select documents, models, and click **Run Extraction**. Mixed document types in one batch automatically use the matching schema and prompt per type.

## Dashboard Tabs

| Tab | Purpose |
|-----|---------|
| **Run** | Select documents and models, run batch extractions with progress tracking |
| **Compare** | Summary metrics table, accuracy/speed/token charts, CSV/JSON export |
| **History** | Browse all past runs, click to expand details, export full history |

## Project Structure

```
config/
  documents/    # YAML metadata for each sample document
  schemas/      # JSON Schema defining extraction targets
  prompts/      # Prompt templates for extraction
  models/       # Model configurations (one YAML per model)
  expected/     # Ground truth JSON for assertions
documents/      # Actual PDF/image files
src/ocr_eval/
  pipeline/     # PDF converter, LiteLLM provider, extraction orchestrator
  evaluation/   # Schema validator, field comparator, accuracy scorer
  models/       # Domain dataclasses and SQLite database layer
  stores/       # Config file loaders
  sample/       # Sample document generators
```

## Adding a Model

Create a YAML file in `config/models/`:

```yaml
id: my_model
name: "My Model"
provider: litellm
model_id: "provider/model-name"  # LiteLLM model string
parameters:
  temperature: 0.0
  max_tokens: 4096
```

See [LiteLLM docs](https://docs.litellm.ai/docs/providers) for supported model strings.

## Adding a Document

1. Place the PDF in `documents/`
2. Create `config/documents/my_doc.yaml` with metadata (id, name, doc_type, file_path)
3. Ensure a schema and prompt exist for the doc_type
4. Optionally add expected output in `config/expected/my_doc.json` for accuracy testing

## Running Tests

```bash
pytest
```
