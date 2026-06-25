import csv
import io
import json

import pandas as pd
import plotly.express as px
import streamlit as st

from ocr_eval.evaluation.scorer import generate_diff_report
from ocr_eval.models.db import (
    export_results,
    get_distinct_document_ids,
    get_distinct_model_ids,
    get_latest_results_by_model,
    get_result_by_run,
    get_run,
    init_db,
    list_runs,
)
from ocr_eval.models.domain import MISSING
from ocr_eval.pipeline.extractor import run_batch_extraction, run_extraction
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
    if st.button("Generate Sample Data", use_container_width=True):
        path = generate_all_sample_data()
        st.success(f"Sample data generated: {path.name}")
        st.rerun()

    st.divider()

    documents = list_documents()
    schemas = list_schemas()
    prompts = list_prompts()
    models = list_models()

tab_run, tab_compare, tab_history = st.tabs(["Run", "Compare", "History"])


# ─── Helpers ───

def _fmt_value(value):
    if value is MISSING:
        return "<missing>"
    if isinstance(value, str):
        return value
    return str(value)


def display_result(result, model_name, doc_name, document_id="", schema_id=""):
    if result.error_message:
        st.error(f"Extraction failed: {result.error_message}")
        return

    st.markdown(f"**{model_name}** → **{doc_name}**")

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
                df, use_container_width=True, hide_index=True,
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


def _export_csv(data: list[dict]) -> str:
    if not data:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    return output.getvalue()


# ─── Tab: Run ───

with tab_run:
    if not documents:
        st.warning("No documents configured. Click 'Generate Sample Data' in the sidebar.")
        st.stop()

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Configuration")

        selected_docs = st.multiselect(
            "Documents", documents, default=documents,
            format_func=lambda d: d.name,
        )

        filtered_doc_types = set(d.doc_type for d in selected_docs) if selected_docs else set()

        filtered_schemas = [s for s in schemas if s.doc_type in filtered_doc_types]
        if not filtered_schemas:
            st.warning("No schemas match selected document types")
            st.stop()
        selected_schema = st.selectbox("Schema", filtered_schemas, format_func=lambda s: s.name)

        filtered_prompts = [p for p in prompts if p.doc_type in filtered_doc_types]
        if not filtered_prompts:
            st.warning("No prompts match selected document types")
            st.stop()
        selected_prompt = st.selectbox("Prompt", filtered_prompts, format_func=lambda p: p.name)

        if not models:
            st.warning("No models configured.")
            st.stop()
        selected_models = st.multiselect(
            "Models", models, default=models,
            format_func=lambda m: m.name,
        )

        if not selected_docs or not selected_models:
            st.info("Select at least one document and one model.")
            st.stop()

        total_runs = len(selected_docs) * len(selected_models)
        st.caption(f"{total_runs} extraction(s) will run")

        run_clicked = st.button("Run Extraction", type="primary", use_container_width=True)

    with col_right:
        if run_clicked:
            doc_ids = [d.id for d in selected_docs]
            model_ids = [m.id for m in selected_models]
            model_names = {m.id: m.name for m in selected_models}
            doc_names = {d.id: d.name for d in selected_docs}

            progress_bar = st.progress(0, text="Starting...")

            def on_progress(step, total, model_id, document_id):
                pct = step / total
                progress_bar.progress(
                    pct,
                    text=f"{step}/{total}: {model_names.get(model_id, model_id)} × {doc_names.get(document_id, document_id)}",
                )

            results = run_batch_extraction(
                doc_ids, selected_schema.id, selected_prompt.id, model_ids,
                progress_callback=on_progress,
            )

            progress_bar.progress(1.0, text=f"Complete — {total_runs} extraction(s)")

            for result in results:
                run = get_run(result.run_id)
                if run:
                    with st.container(border=True):
                        display_result(
                            result,
                            model_names.get(run.model_id, run.model_id),
                            doc_names.get(run.document_id, run.document_id),
                            run.document_id,
                            run.schema_id,
                        )
        else:
            st.info("Select documents and models, then click 'Run Extraction'.")


# ─── Tab: Compare ───

with tab_compare:
    completed_model_ids = get_distinct_model_ids()
    completed_doc_ids = get_distinct_document_ids()

    if not completed_model_ids:
        st.info("No completed runs yet. Run some extractions first.")
    else:
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            compare_models = st.multiselect(
                "Models to compare", completed_model_ids, default=completed_model_ids,
                key="compare_models",
            )
        with col_filter2:
            compare_docs = st.multiselect(
                "Documents to include", completed_doc_ids, default=completed_doc_ids,
                key="compare_docs",
            )

        if compare_models and compare_docs:
            data = get_latest_results_by_model(compare_models, compare_docs)

            if not data:
                st.warning("No results found for the selected filters.")
            else:
                df = pd.DataFrame(data)

                # Summary metrics table
                st.subheader("Summary")
                summary = df.groupby("model_id").agg(
                    avg_accuracy=("accuracy_score", "mean"),
                    avg_time=("wall_clock_seconds", "mean"),
                    avg_tokens=("total_tokens", "mean"),
                    total_tokens=("total_tokens", "sum"),
                    runs=("model_id", "count"),
                ).reset_index()
                summary.columns = ["Model", "Avg Accuracy", "Avg Time (s)", "Avg Tokens", "Total Tokens", "Runs"]
                summary["Avg Accuracy"] = summary["Avg Accuracy"].map(lambda x: f"{x:.1%}")
                summary["Avg Time (s)"] = summary["Avg Time (s)"].map(lambda x: f"{x:.2f}")
                summary["Avg Tokens"] = summary["Avg Tokens"].map(lambda x: f"{x:,.0f}")
                summary["Total Tokens"] = summary["Total Tokens"].map(lambda x: f"{x:,.0f}")
                st.dataframe(summary, use_container_width=True, hide_index=True)

                # Charts
                st.subheader("Comparison Charts")
                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    fig_acc = px.bar(
                        df, x="document_id", y="accuracy_score", color="model_id",
                        barmode="group", title="Accuracy by Document",
                        labels={"accuracy_score": "Accuracy", "document_id": "Document", "model_id": "Model"},
                    )
                    fig_acc.update_yaxes(tickformat=".0%", range=[0, 1.05])
                    st.plotly_chart(fig_acc, use_container_width=True)

                with chart_col2:
                    fig_speed = px.bar(
                        df, x="document_id", y="wall_clock_seconds", color="model_id",
                        barmode="group", title="Speed by Document",
                        labels={"wall_clock_seconds": "Time (s)", "document_id": "Document", "model_id": "Model"},
                    )
                    st.plotly_chart(fig_speed, use_container_width=True)

                chart_col3, chart_col4 = st.columns(2)

                with chart_col3:
                    token_df = df.melt(
                        id_vars=["model_id", "document_id"],
                        value_vars=["input_tokens", "output_tokens"],
                        var_name="token_type", value_name="tokens",
                    )
                    token_df["token_type"] = token_df["token_type"].map(
                        {"input_tokens": "Input", "output_tokens": "Output"}
                    )
                    fig_tokens = px.bar(
                        token_df, x="model_id", y="tokens", color="token_type",
                        barmode="stack", title="Token Usage by Model",
                        labels={"tokens": "Tokens", "model_id": "Model", "token_type": "Type"},
                    )
                    st.plotly_chart(fig_tokens, use_container_width=True)

                with chart_col4:
                    fig_total = px.bar(
                        df, x="model_id", y="total_tokens", color="document_id",
                        barmode="group", title="Total Tokens by Model & Document",
                        labels={"total_tokens": "Total Tokens", "model_id": "Model", "document_id": "Document"},
                    )
                    st.plotly_chart(fig_total, use_container_width=True)

                # Export from compare tab
                st.subheader("Export")
                exp_col1, exp_col2 = st.columns(2)
                with exp_col1:
                    csv_data = _export_csv(data)
                    st.download_button(
                        "Download CSV", csv_data, "comparison_results.csv",
                        mime="text/csv", use_container_width=True,
                    )
                with exp_col2:
                    json_data = json.dumps(data, indent=2, default=str)
                    st.download_button(
                        "Download JSON", json_data, "comparison_results.json",
                        mime="application/json", use_container_width=True,
                    )


# ─── Tab: History ───

with tab_history:
    runs = list_runs()
    if not runs:
        st.info("No runs yet. Select a configuration and click 'Run Extraction' in the Run tab.")
    else:
        # Export all
        exp_col1, exp_col2, _ = st.columns([1, 1, 3])
        all_export = export_results()
        with exp_col1:
            st.download_button(
                "Export All CSV", _export_csv(all_export), "all_results.csv",
                mime="text/csv", use_container_width=True,
            )
        with exp_col2:
            st.download_button(
                "Export All JSON", json.dumps(all_export, indent=2, default=str),
                "all_results.json", mime="application/json", use_container_width=True,
            )

        st.divider()

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
