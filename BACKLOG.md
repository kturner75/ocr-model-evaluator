# Backlog

## Completed

### Goal 1: End-to-End Single Extraction
- [x] Project scaffolding (Python package, deps, SQLite, config)
- [x] Core data models (Document, Schema, Prompt, ModelConfig, Run, Result)
- [x] Document store — add/list/view sample PDFs
- [x] Schema manager — define JSON schemas per document type
- [x] Prompt manager — configure extraction prompt templates
- [x] LiteLLM integration for unified model access
- [x] Model registry — add/configure/list models
- [x] PDF-to-model pipeline — PDF pages to base64 images via PyMuPDF
- [x] Single document extraction — doc + prompt + schema → model → JSON
- [x] Metrics capture — wall clock time, token usage
- [x] Response parsing — JSON extraction with code fence fallback
- [x] Schema validation via jsonschema
- [x] Field-level exact match assertion engine
- [x] Accuracy scoring and diff reporting
- [x] Sample invoice PDF generator with known ground truth
- [x] Streamlit dashboard with results display

### Goal 2: Batch Runs, Comparison & Export
- [x] Batch extraction across docs × models with progress tracking
- [x] 3-tab dashboard (Run / Compare / History)
- [x] Model comparison charts (accuracy, speed, tokens) via Plotly
- [x] Summary metrics table with aggregated stats
- [x] CSV and JSON export from Compare and History tabs
- [x] GPT-4o-mini model config
- [x] Claude Sonnet 4.6 model config

## Up Next

### Goal 3: Real-World Testing & More Models
- [x] Expand sample suite beyond single invoice (receipt, purchase order, multi-page invoice)
- [x] Schemas + prompts per document type; batch runs resolve schema/prompt by doc_type
- [ ] Add harder real-world samples (scanned/degraded, fax-style, handwritten annotations)
- [ ] Add Ollama local model configs for open-source comparison
- [ ] Add Mistral model config
- [ ] Add Deepseek model config


### Goal 4: Custom Provider Adapters
- [ ] Implement provider adapter for Baidu Unlimited OCR
- [ ] Implement provider adapter for other non-LiteLLM OCR services
- [ ] Document how to write a custom adapter

### Goal 5: Enhanced Assertion Framework
- [ ] Fuzzy/partial string matching (e.g., "Acme Corp" ≈ "ACME Corporation")
- [ ] Regex pattern matching for fields
- [ ] Semantic similarity comparison
- [ ] Type/format checks (valid ISO date, valid email, etc.)
- [ ] Array order-insensitive matching

### Goal 6: Cost & Trends
- [ ] Cost estimation per run based on model pricing
- [ ] Cost column in comparison charts and export
- [ ] Run history trends — accuracy/speed over time per model
- [ ] Trend charts in Compare tab

### Goal 7: Configuration UI
- [ ] Add/edit model configs from the dashboard (instead of YAML files)
- [ ] Add/edit schemas and prompts from the dashboard
- [ ] Upload documents via the dashboard
- [ ] Configure expected outputs via the dashboard

### Ideas / Future
- [ ] Parallel model execution for faster batch runs
- [ ] Confidence scoring from model responses
- [ ] Support for image files (PNG, JPEG, TIFF) alongside PDF
- [ ] A/B prompt testing — compare extraction quality across different prompts
- [ ] Webhook/notification on batch completion
