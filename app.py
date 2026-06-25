import json

import pandas as pd
import streamlit as st

from ocr_eval.evaluation.scorer import generate_diff_report
from ocr_eval.models.db import get_result_by_run, get_run, init_db, list_runs
from ocr_eval.models.domain import MISSING, RunStatus
from ocr_eval.pipeline.extractor import run_extraction
from ocr_eval.sample.generate_invoice import generate_all_sample_data
from ocr_eval.stores.document_store import list_documents
from ocr_eval.stores.expected_store import get_expected
from ocr_eval.stores.model_store import list_models
from ocr_eval.stores.prompt_store import list_prompts
from ocr_eval.stores.schema_store import list_schemas

init_db()

st.set_page_config(page_title="OCR Model Evaluator", page_icon="🔍", layout="wide")
st.title("OCR Model Evaluator")

with st.sidebar:
    st.header("Configuration")

    if st.button("Generate Sample Data", use_container_width=True):
        path = generate_all_sample_data()
        st.success(f"Sample data generated: {path.name}")
        st.rerun()

    st.divider()

    documents = list_documents()
    schemas = list_schemas()
    prompts = list_prompts()
    models = list_models()

    if not documents:
        st.warning("No documents configured. Click 'Generate Sample Data' to get started.")
        st.stop()

    selected_doc = st.selectbox("Document", documents, format_func=lambda d: d.name)
    filtered_schemas = [s for s in schemas if s.doc_type == selected_doc.doc_type]
    if not filtered_schemas:
        st.warning(f"No schemas for doc type '{selected_doc.doc_type}'")
        st.stop()
    selected_schema = st.selectbox("Schema", filtered_schemas, format_func=lambda s: s.name)

    filtered_prompts = [p for p in prompts if p.doc_type == selected_doc.doc_type]
    if not filtered_prompts:
        st.warning(f"No prompts for doc type '{selected_doc.doc_type}'")
        st.stop()
    selected_prompt = st.selectbox("Prompt", filtered_prompts, format_func=lambda p: p.name)

    if not models:
        st.warning("No models configured.")
        st.stop()
    selected_model = st.selectbox("Model", models, format_func=lambda m: m.name)

    st.divider()
    run_clicked = st.button("Run Extraction", type="primary", use_container_width=True)


def display_result(result, model_name, doc_name, document_id="", schema_id=""):
    if result.error_message:
        st.error(f"Extraction failed: {result.error_message}")
        return

    st.subheader(f"{model_name} → {doc_name}")

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Accuracy", f"{result.accuracy_score:.1%}")
    col2.metric("Time", f"{result.wall_clock_seconds:.2f}s")
    col3.metric("Input Tokens", f"{result.input_tokens:,}")
    col4.metric("Output Tokens", f"{result.output_tokens:,}")
    col5.metric("Total Tokens", f"{result.total_tokens:,}")

    tab_results, tab_fields, tab_validation, tab_raw = st.tabs(
        ["Results", "Field Comparison", "Validation", "Raw Response"]
    )

    with tab_results:
        left, right = st.columns(2)
        with left:
            st.markdown("**Expected**")
            expected = get_expected(document_id, schema_id) if document_id and schema_id else None
            if expected:
                st.json(expected)
            else:
                st.info("No expected output configured")
        with right:
            st.markdown("**Extracted**")
            if result.extracted_json:
                st.json(result.extracted_json)

    with tab_fields:
        if result.field_results:
            rows = []
            for fr in result.field_results:
                rows.append({
                    "Status": "✅" if fr.match else "❌",
                    "Field": fr.field_path,
                    "Expected": _fmt_value(fr.expected_value),
                    "Actual": _fmt_value(fr.actual_value),
                })
            df = pd.DataFrame(rows)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={"Status": st.column_config.TextColumn(width="small")},
            )

            with st.expander("Text Report"):
                st.code(generate_diff_report(result.field_results))
        else:
            st.info("No field comparison available (no expected output configured)")

    with tab_validation:
        if result.is_valid:
            st.success("JSON output is valid against the schema")
        else:
            st.error("JSON output has validation errors")
            for err in result.validation_errors:
                st.markdown(f"- `{err}`")

    with tab_raw:
        if result.extracted_json:
            st.code(json.dumps(result.extracted_json, indent=2), language="json")


def _fmt_value(value):
    if value is MISSING:
        return "<missing>"
    if isinstance(value, str):
        return value
    return str(value)


if run_clicked:
    with st.status("Running extraction...", expanded=True) as status:
        st.write("Loading document and configuration...")
        st.write(f"Model: **{selected_model.name}** | Document: **{selected_doc.name}**")
        st.write("Converting PDF to images...")
        st.write("Calling model API...")

        result = run_extraction(
            selected_doc.id, selected_schema.id, selected_prompt.id, selected_model.id
        )

        if result.error_message:
            status.update(label="Extraction failed", state="error")
        else:
            status.update(label=f"Extraction complete — {result.accuracy_score:.1%} accuracy", state="complete")

    display_result(result, selected_model.name, selected_doc.name, selected_doc.id, selected_schema.id)


st.divider()
st.subheader("Run History")

runs = list_runs()
if not runs:
    st.info("No runs yet. Select a configuration and click 'Run Extraction'.")
else:
    history_rows = []
    for run in runs:
        result = get_result_by_run(run.id)
        history_rows.append({
            "Timestamp": run.created_at or "",
            "Model": run.model_id,
            "Document": run.document_id,
            "Status": run.status.value,
            "Accuracy": f"{result.accuracy_score:.1%}" if result and not result.error_message else "—",
            "Time (s)": f"{result.wall_clock_seconds:.2f}" if result and not result.error_message else "—",
            "Tokens": f"{result.total_tokens:,}" if result and not result.error_message else "—",
            "run_id": run.id,
        })

    df_history = pd.DataFrame(history_rows)

    selected_run_idx = st.dataframe(
        df_history.drop(columns=["run_id"]),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if selected_run_idx and selected_run_idx.selection and selected_run_idx.selection.rows:
        idx = selected_run_idx.selection.rows[0]
        run_id = history_rows[idx]["run_id"]
        run = get_run(run_id)
        result = get_result_by_run(run_id)
        if run and result:
            st.divider()
            display_result(result, run.model_id, run.document_id, run.document_id, run.schema_id)
