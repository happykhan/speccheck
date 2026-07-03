from collections import OrderedDict
from html import escape

import pandas as pd

PASS_VALUES = {"passed", "true", "1", "yes"}
FAIL_VALUES = {"failed", "false", "0", "no"}


def normalize_status(value):
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in PASS_VALUES:
        return True
    if normalized in FAIL_VALUES:
        return False
    return None


def status_label(value):
    normalized = normalize_status(value)
    if normalized is True:
        return "PASSED"
    if normalized is False:
        return "FAILED"
    return ""


def safe_anchor(value):
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")


def format_numeric(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return f"{int(value):,}"
        return f"{float(value):,.2f}"
    return str(value)


def infer_value_type(series):
    non_null = series.dropna()
    if non_null.empty:
        return "string"
    if pd.api.types.is_bool_dtype(non_null):
        return "status"
    if pd.api.types.is_numeric_dtype(non_null):
        return "numeric"
    if non_null.map(lambda value: normalize_status(value) is not None).all():
        return "status"
    return "string"


def dataframe_to_interactive_table(df, table_id, searchable=True, interactive=True):
    rendered_df = df.copy()
    column_types = {}
    for column in rendered_df.columns:
        column_types[column] = infer_value_type(rendered_df[column])
        if column_types[column] == "status":
            rendered_df[column] = rendered_df[column].map(status_label)
        elif column_types[column] == "numeric":
            rendered_df[column] = rendered_df[column].map(format_numeric)
        else:
            rendered_df[column] = rendered_df[column].fillna("").astype(str)

    thead = "".join(
        f'<th data-type="{column_types[column]}">{escape(str(column))}</th>'
        for column in rendered_df.columns
    )
    rows = []
    for _, row in rendered_df.iterrows():
        cells = []
        for column in rendered_df.columns:
            raw_value = row[column]
            css_class = ""
            if raw_value == "PASSED":
                css_class = "qc-pass"
            elif raw_value == "FAILED":
                css_class = "qc-fail"
            cells.append(f'<td class="{css_class}">{escape(str(raw_value))}</td>')
        rows.append(f"<tr>{''.join(cells)}</tr>")

    filter_box = ""
    if searchable and interactive:
        filter_box = (
            f'<div class="table-tools"><label for="{table_id}-filter">Filter</label>'
            f'<input id="{table_id}-filter" class="table-filter" type="search" '
            f'placeholder="Filter rows" data-target="{table_id}" /></div>'
        )

    table_class = "table report-table"
    if interactive:
        table_class += " js-sort-filter"

    return (
        f'{filter_box}<div class="table-container">'
        f'<table id="{table_id}" class="{table_class}">'
        f"<thead><tr>{thead}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
    )


def get_sum_table(df):
    sum_table = df[[col for col in df.columns if col.endswith("all_checks_passed")]].copy()
    sum_table["QC_PASS"] = sum_table.apply(
        lambda row: all(
            normalize_status(value) is not False
            for value in row
            if normalize_status(value) is not None
        ),
        axis=1,
    )
    for column in sum_table.columns:
        sum_table[column] = sum_table[column].map(status_label)
    sum_table["QC_PASS"] = sum_table["QC_PASS"].map(status_label)
    sum_table.columns = sum_table.columns.str.replace(".all_checks_passed", "", regex=False)
    return sum_table


def make_sample_counts(df):
    sum_table = get_sum_table(df)
    total_samples = len(sum_table)
    pass_count = sum_table["QC_PASS"].value_counts().get("PASSED", 0)
    fail_count = sum_table["QC_PASS"].value_counts().get("FAILED", 0)
    pass_percentage = (pass_count / total_samples) * 100 if total_samples > 0 else 0
    return (
        f"There are {total_samples} samples included with "
        f"<span class='qc-pass-text'>{pass_count} passing</span> and "
        f"<span class='qc-fail-text'>{fail_count} failing</span> "
        f"({pass_percentage:.2f}% pass rate)."
    )


def summary_table(df, interactive_tables=True):
    sum_table = get_sum_table(df)
    table_html = dataframe_to_interactive_table(
        sum_table.reset_index().rename(columns={"index": "Sample"}),
        table_id="summary-table",
        interactive=interactive_tables,
    )
    explanation = "<p>This table shows the overall QC status for each sample.</p>"
    if interactive_tables:
        explanation = (
            "<p>This table shows the overall QC status for each sample. "
            "Click headers to sort and use the filter box to search rows.</p>"
        )
    return explanation + table_html


def get_failure_reasons(df, software_dict):
    sum_table = get_sum_table(df)
    failure_columns = [
        column for column in sum_table.columns if column not in {"QC_PASS", "all_checks_passed"}
    ]
    failure_reasons = sum_table[sum_table["QC_PASS"] == "FAILED"][failure_columns].apply(
        lambda series: series == "FAILED"
    )
    top_failure_reasons = failure_reasons.sum().sort_values(ascending=False).head(5)
    top_failure_reasons = pd.to_numeric(top_failure_reasons, errors="coerce").fillna(0)
    top_failure_reasons = top_failure_reasons[top_failure_reasons > 0]
    if len(top_failure_reasons) == 0:
        return "<p>No recurring failure reasons were detected.</p>"
    failure_string = (
        "<p>This was the top reason for failure:</p>"
        if len(top_failure_reasons) == 1
        else f"<p>These were the top {len(top_failure_reasons)} reasons for failure:</p>"
    )
    explanation = failure_string + "<ol>"
    for reason, count in top_failure_reasons.items():
        if reason not in software_dict:
            continue
        name = software_dict.get(reason)["name"]
        explanation += (
            f'<li><b><a href="#{safe_anchor(name)}">{name}</a></b>: {int(count)} failures</li>'
        )
    return explanation + "</ol>"


def build_metric_summary_frames(df):
    categories = OrderedDict(
        [
            (
                "Species assignment",
                [
                    "Speciator.speciesName",
                    "Speciator.confidence",
                    "Sylph.top_species",
                    "Sylph.top_taxonomic_abundance",
                ],
            ),
            (
                "Assembly quality",
                [
                    "Quast.N50",
                    "Quast.# contigs (>= 0 bp)",
                    "Quast.Total length",
                    "Quast.GC (%)",
                    "Quast.Largest contig",
                ],
            ),
            (
                "Completeness and contamination",
                [
                    "Checkm.Completeness",
                    "Checkm.Contamination",
                    "Checkm.GC",
                    "Checkm.Genome size (bp)",
                ],
            ),
            (
                "Coverage and abundance",
                [
                    "Depth.Depth",
                    "Depth.Read_type",
                    "Sylph.number_of_genomes",
                    "Ariba.percent",
                ],
            ),
        ]
    )

    frames = OrderedDict()
    for category, columns in categories.items():
        rows = []
        for column in columns:
            if column not in df.columns:
                continue
            series = df[column]
            numeric = pd.to_numeric(series, errors="coerce")
            if numeric.notna().any():
                rows.append(
                    {
                        "Metric": column,
                        "Min": format_numeric(numeric.min()),
                        "Median": format_numeric(numeric.median()),
                        "Max": format_numeric(numeric.max()),
                        "Missing": int(series.isna().sum()),
                    }
                )
                continue
            normalized = series.dropna().astype(str)
            if normalized.empty:
                continue
            rows.append(
                {
                    "Metric": column,
                    "Most common": normalized.mode().iloc[0],
                    "Unique values": int(normalized.nunique()),
                    "Missing": int(series.isna().sum()),
                }
            )
        if rows:
            frames[category] = pd.DataFrame(rows)
    return frames


def render_metric_summary_tables(summary_frames, qualifyr_style=False, interactive_tables=True):
    if not summary_frames:
        return ""
    intro = "<p>Compact summary tables give a quick view of key QC metrics across the dataset.</p>"
    if qualifyr_style:
        intro = (
            "<p>Compact summary tables are rendered in a built-in qualifyr-style layout "
            "for quick manuscript-friendly comparison across samples.</p>"
        )
    sections = ['<section class="metric-summary-grid">']
    for index, (category, frame) in enumerate(summary_frames.items(), start=1):
        sections.append(
            '<article class="metric-summary-card">'
            f"<h3>{escape(category)}</h3>"
            f"{dataframe_to_interactive_table(frame, f'metric-summary-{index}', searchable=False, interactive=interactive_tables)}"
            "</article>"
        )
    sections.append("</section>")
    return intro + "".join(sections)


def export_summary_workbook(report_df, output_path, summary_frames):
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        report_df.to_excel(writer, sheet_name="report", index=False)
        get_sum_table(report_df.set_index("sample_id")).reset_index().rename(
            columns={"index": "sample_id"}
        ).to_excel(writer, sheet_name="qc_status", index=False)
        for sheet_index, (category, frame) in enumerate(summary_frames.items(), start=1):
            safe_name = category[:31] if len(category) <= 31 else category[:28] + "..."
            frame.to_excel(writer, sheet_name=safe_name or f"sheet{sheet_index}", index=False)


def build_qualifyr_style_table(df, interactive_tables=True):
    preferred_columns = [
        "sample_id",
        "Speciator.speciesName",
        "Speciator.confidence",
        "Quast.N50",
        "Quast.# contigs (>= 0 bp)",
        "Quast.Total length",
        "Checkm.Completeness",
        "Checkm.Contamination",
        "all_checks_passed",
    ]
    available_columns = [column for column in preferred_columns if column in df.columns]
    if not available_columns:
        return ""
    qualifyr_df = df[available_columns].copy()
    if "all_checks_passed" in qualifyr_df.columns:
        qualifyr_df["all_checks_passed"] = qualifyr_df["all_checks_passed"].map(status_label)
    html = "<p>This compact table uses a qualifyr-like layout for fast sample review.</p>"
    return html + dataframe_to_interactive_table(
        qualifyr_df, "qualifyr-style-table", interactive=interactive_tables
    )
