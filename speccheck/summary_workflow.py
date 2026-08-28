"""Summary workflow: merge collected samples and serialize report artifacts."""

from __future__ import annotations

import logging
import os

import pandas as pd

from speccheck.qualibact import add_qualibact_compatibility_columns
from speccheck.report import plot_charts
from speccheck.report_tables import (
    build_concise_report_frame,
    build_full_report_frame,
    build_metric_summary_frames,
    combine_qc_statuses,
    export_summary_workbook,
    status_label,
)


def summary(
    directory,
    output,
    species,
    sample_id,
    template,
    plot=False,
    xlsx_output=None,
    interactive_tables=True,
    qualifyr_style=False,
    qualibact_compat=False,
):
    """Merge collected CSVs and write concise, full, HTML, and XLSX reports."""
    os.makedirs(output, exist_ok=True)
    csv_files = discover_summary_csvs(directory, output)
    merged_data = merge_summary_csvs(csv_files, sample_id)
    if not merged_data:
        logging.error("No data found in the merged files.")
        return

    report_df = _build_report_frame(merged_data)
    if qualibact_compat:
        report_df = add_qualibact_compatibility_columns(report_df)
    report_df = decorate_report_dataframe(report_df)
    concise_report_df = build_concise_report_frame(report_df)
    full_report_df = build_full_report_frame(report_df)
    normalized_full_df = normalize_report_status_columns(full_report_df)
    normalized_concise_df = normalize_report_status_columns(concise_report_df)

    normalized_concise_df.to_csv(os.path.join(output, "report.csv"), index=False)
    normalized_full_df.to_csv(os.path.join(output, "report.full.csv"), index=False)

    if plot:
        plot_dict = {
            str(row["sample_id"]): row
            for row in report_df.to_dict(orient="records")
            if "sample_id" in row
        }
        _report_df, summary_frames = plot_charts(
            plot_dict,
            species,
            output_html_path=os.path.join(output, "report.html"),
            input_template_path=template,
            interactive_tables=interactive_tables,
            qualifyr_style=qualifyr_style,
        )
        legacy_stylesheet = os.path.join(output, "bulma.css")
        if os.path.exists(legacy_stylesheet):
            os.remove(legacy_stylesheet)
        logging.info("Plots generated.")
    else:
        summary_frames = build_metric_summary_frames(report_df)

    if xlsx_output:
        export_summary_workbook(
            normalized_concise_df, normalized_full_df, xlsx_output, summary_frames
        )
        logging.info("Wrote XLSX summary to %s", xlsx_output)


def _build_report_frame(merged_data):
    logging.info("Merged data for %d samples", len(merged_data))
    all_fieldnames = {field for values in merged_data.values() for field in values}
    check_columns = sorted(field for field in all_fieldnames if field.endswith(".check"))
    other_columns = sorted(field for field in all_fieldnames if not field.endswith(".check"))
    fieldnames = ["sample_id", *check_columns, *other_columns]
    rows = [
        {"sample_id": current_sample, **merged_data[current_sample]}
        for current_sample in sorted(merged_data)
    ]
    return pd.DataFrame(rows).reindex(columns=[field for field in fieldnames if field in rows[0]])


def discover_summary_csvs(directory, output):
    """Find summary inputs while excluding detailed and generated artifacts."""
    csv_files = []
    skipped_detailed = []
    input_root = os.path.abspath(directory)
    output_root = os.path.abspath(output)

    for root, _dirs, files in os.walk(directory):
        abs_root = os.path.abspath(root)
        if abs_root == output_root or abs_root.startswith(output_root + os.sep):
            continue
        for filename in files:
            if not filename.endswith(".csv"):
                continue
            path = os.path.join(root, filename)
            if filename.startswith("detailed."):
                skipped_detailed.append(path)
                continue
            if os.path.abspath(path) in {
                os.path.join(output_root, "report.csv"),
                os.path.join(output_root, "report.full.csv"),
            }:
                continue
            csv_files.append(path)

    if skipped_detailed:
        logging.info(
            "Ignoring %d detailed CSV file(s) during summary merge; concise CSVs are used.",
            len(skipped_detailed),
        )
    if not csv_files:
        detail = " Only detailed.*.csv files were found." if skipped_detailed else ""
        raise ValueError(f"No summary input CSV files found under {input_root}.{detail}")
    return sorted(csv_files)


def merge_summary_csvs(csv_files, sample_id):
    """Merge sample CSVs and reject ambiguous sample identifiers."""
    merged_data = {}
    seen_samples = {}
    for path in csv_files:
        header = pd.read_csv(path, nrows=0)
        identifier_columns = [
            column
            for column in header.columns
            if column == sample_id or column.lower().endswith((".sample_id", ".sampleid"))
        ]
        frame = pd.read_csv(path, dtype=dict.fromkeys(identifier_columns, "string"))
        if sample_id not in frame.columns:
            raise ValueError(
                f"Summary input {path} is missing required sample column '{sample_id}'."
            )
        if frame[sample_id].isna().any():
            raise ValueError(f"Summary input {path} contains missing sample IDs in '{sample_id}'.")
        sample_values = frame[sample_id].astype(str)
        blank = sample_values.str.strip().eq("")
        if blank.any():
            raise ValueError(f"Summary input {path} contains blank sample IDs in '{sample_id}'.")
        padded = sample_values.ne(sample_values.str.strip())
        if padded.any():
            raise ValueError(
                f"Summary input {path} contains sample IDs with surrounding whitespace "
                f"in '{sample_id}'."
            )
        duplicated = frame[frame[sample_id].duplicated(keep=False)][sample_id].astype(str).tolist()
        if duplicated:
            duplicate_names = ", ".join(sorted(set(duplicated)))
            raise ValueError(
                f"Summary input {path} contains duplicate sample IDs: {duplicate_names}"
            )
        for row in frame.to_dict(orient="records"):
            current_sample = str(row.pop(sample_id))
            embedded_sample_columns = [
                column for column in row if column.lower().endswith((".sample_id", ".sampleid"))
            ]
            for column in embedded_sample_columns:
                embedded_sample = row[column]
                if pd.isna(embedded_sample):
                    continue
                if str(embedded_sample) != current_sample:
                    raise ValueError(
                        f"Sample ID mismatch in {path}: '{sample_id}' is "
                        f"'{current_sample}', but '{column}' is '{embedded_sample}'."
                    )
            if current_sample in seen_samples:
                raise ValueError(
                    f"Duplicate sample ID '{current_sample}' found in both "
                    f"{seen_samples[current_sample]} and {path}."
                )
            seen_samples[current_sample] = path
            merged_data[current_sample] = row
    return merged_data


def normalize_report_status_columns(report_df):
    """Write status-like report columns consistently."""
    normalized = report_df.copy()
    status_columns = [
        column
        for column in normalized.columns
        if column.endswith(".check")
        or column.endswith(".status")
        or column.endswith(".qc_status")
        or column.endswith("_qc")
        or column.endswith("all_checks_passed")
    ]
    for column in status_columns:
        normalized[column] = normalized[column].map(lambda value: status_label(value) or value)
    for column in (
        "speccheck_fail_on_not_evaluated",
        "speccheck_species_checks_available",
        "speccheck_threshold_fallback_used",
    ):
        if column not in normalized.columns:
            continue
        normalized[column] = normalized[column].map(_yes_no_label)
    return normalized


def _yes_no_label(value):
    if pd.isna(value):
        return ""
    normalized = str(value).strip().lower()
    if normalized in {"true", "yes", "1"}:
        return "YES"
    if normalized in {"false", "no", "0"}:
        return "NO"
    return value


def decorate_report_dataframe(report_df):
    decorated = report_df.copy()
    for column in list(decorated.columns):
        if not column.endswith(".all_checks_passed"):
            continue
        software = column.removesuffix(".all_checks_passed")
        metric_statuses = [
            decorated[metric]
            for metric in decorated.columns
            if metric.startswith(f"{software}.") and metric.endswith((".status", ".check"))
        ]
        decorated[f"{software}.qc_status"] = pd.concat(
            [decorated[column], *metric_statuses], axis=1
        ).apply(lambda row: combine_qc_statuses(*row), axis=1)
    decorated["speccheck_qc"] = decorated.apply(_row_speccheck_qc_label, axis=1)
    if "qualibact_compat_tier" in decorated.columns:
        decorated["qualibact_qc"] = decorated["qualibact_compat_tier"].map(status_label)
    if "qualibact_tier" in decorated.columns:
        decorated["historical_qualibact_qc"] = decorated["qualibact_tier"].map(status_label)
    decorated["overall_qc"] = decorated.apply(_row_overall_qc_label, axis=1)
    aliases = {
        "Speciator.speciesName": "species",
        "Speciator.confidence": "species_confidence",
        "speccheck_threshold_source": "threshold_source",
    }
    for source, target in aliases.items():
        if source in decorated.columns and target not in decorated.columns:
            decorated[target] = decorated[source]
    decorated["reason_summary"] = decorated.apply(_row_reason_summary, axis=1)
    return decorated


def _row_overall_qc_label(row):
    return combine_qc_statuses(row.get("speccheck_qc"), row.get("qualibact_qc"))


def _row_speccheck_qc_label(row):
    if pd.notna(row.get("speccheck_qc")):
        return status_label(row.get("speccheck_qc"))
    if pd.notna(row.get("speccheck_overall_status")):
        return status_label(row.get("speccheck_overall_status"))
    return status_label(row.get("all_checks_passed"))


def _row_reason_summary(row):
    reasons = []
    speccheck_qc = status_label(row.get("speccheck_qc"))
    if speccheck_qc == "FAIL":
        reasons.extend(_split_reasons(row.get("speccheck_failure_reasons")))
    elif speccheck_qc == "WARN":
        reasons.extend(_split_reasons(row.get("speccheck_warning_reasons")))

    if status_label(row.get("qualibact_qc")) in {"WARN", "FAIL"}:
        reasons.extend(_split_reasons(row.get("qualibact_compat_reasons")))

    if not reasons and speccheck_qc in {"WARN", "FAIL"}:
        reasons = []
        for column, value in row.items():
            if not column.endswith((".check", ".status")):
                continue
            if status_label(value) != speccheck_qc:
                continue
            reasons.append(column.removesuffix(".check").removesuffix(".status"))
    return "; ".join(dict.fromkeys(reasons)) or "none"


def _split_reasons(value):
    if pd.isna(value) or str(value).strip().lower() in {"", "none"}:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]
