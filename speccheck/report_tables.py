from collections import OrderedDict
from html import escape

import pandas as pd

REPORT_SCHEMA_VERSION = "1.0"

PASS_VALUES = {"pass", "passed", "true", "1", "yes"}
FAIL_VALUES = {"fail", "failed", "false", "0", "no"}
WARN_VALUES = {"warn", "warning"}
NOT_EVALUATED_VALUES = {
    "not_available",
    "not available",
    "not-available",
    "not_evaluated",
    "not evaluated",
    "not-evaluated",
}


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
    if is_not_evaluated(value):
        return "NOT_EVALUATED"
    normalized_text = str(value).strip().upper() if not pd.isna(value) else ""
    if normalized_text.lower() in WARN_VALUES:
        return "WARN"
    normalized = normalize_status(value)
    if normalized is True:
        return "PASS"
    if normalized is False:
        return "FAIL"
    return ""


def is_not_evaluated(value):
    if pd.isna(value):
        return False
    return str(value).strip().lower() in NOT_EVALUATED_VALUES


def is_status_like(value):
    if pd.isna(value):
        return False
    return (
        normalize_status(value) is not None
        or str(value).strip().lower() in WARN_VALUES
        or is_not_evaluated(value)
    )


def status_rank(value):
    label = status_label(value)
    if label == "FAIL":
        return 0
    if label in {"NOT_EVALUATED", "WARN"}:
        return 1
    if label == "PASS":
        return 2
    return -1


def combine_qc_statuses(*values):
    """Return the worst evaluated QC status using the public status vocabulary.

    NOT_EVALUATED is returned only when no evaluated status is available. This
    means an unavailable optional compatibility scheme does not obscure a valid
    native Speccheck result.
    """
    labels = [status_label(value) for value in values]
    evaluated = [label for label in labels if label in {"PASS", "WARN", "FAIL"}]
    if evaluated:
        return min(evaluated, key=status_rank)
    if "NOT_EVALUATED" in labels:
        return "NOT_EVALUATED"
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
    if non_null.map(is_status_like).all():
        return "status"
    return "string"


def dataframe_to_interactive_table(
    df,
    table_id,
    searchable=True,
    interactive=True,
    page_size=50,
    row_status_column=None,
    row_id_column=None,
    clickable_rows=False,
):
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
            if raw_value == "PASS":
                css_class = "qc-pass"
            elif raw_value == "FAIL":
                css_class = "qc-fail"
            elif raw_value == "WARN":
                css_class = "qc-warn"
            elif raw_value == "NOT_EVALUATED":
                css_class = "qc-not-evaluated"
            cells.append(f'<td class="{css_class}">{escape(str(raw_value))}</td>')
        attributes = []
        if row_status_column and row_status_column in rendered_df.columns:
            attributes.append(f'data-qc-status="{escape(str(row[row_status_column]))}"')
        if row_id_column and row_id_column in rendered_df.columns:
            attributes.append(f'data-sample-id="{escape(str(row[row_id_column]))}"')
        if clickable_rows:
            attributes.extend(
                [
                    'class="sample-review-row"',
                    'tabindex="0"',
                    'role="button"',
                    f'aria-label="Open details for {escape(str(row[row_id_column]))}"',
                ]
            )
        row_attributes = f" {' '.join(attributes)}" if attributes else ""
        rows.append(f"<tr{row_attributes}>{''.join(cells)}</tr>")

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

    pagination = ""
    page_size_attr = ""
    if interactive and page_size and len(rendered_df) > page_size:
        page_size_attr = f' data-page-size="{int(page_size)}" data-current-page="1"'
        pagination = (
            f'<div class="table-pagination" data-target="{table_id}">'
            '<button type="button" class="table-page-prev">Previous</button>'
            '<span class="table-page-status"></span>'
            '<button type="button" class="table-page-next">Next</button>'
            "</div>"
        )

    return (
        f'{filter_box}<div class="table-container">'
        f'<table id="{table_id}" class="{table_class}"{page_size_attr}>'
        f"<thead><tr>{thead}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"
        f"{pagination}"
    )


def get_sum_table(df):
    status_columns = [
        col for col in df.columns if col == "overall_qc" or col.endswith(".qc_status")
    ]
    if not status_columns:
        status_columns = [col for col in df.columns if col.endswith("all_checks_passed")]
    sum_table = df[status_columns].copy()
    for column in sum_table.columns:
        sum_table[column] = sum_table[column].map(status_label)
    if "overall_qc" in sum_table.columns:
        sum_table["QC"] = sum_table.pop("overall_qc")
    else:
        sum_table["QC"] = sum_table.apply(lambda row: combine_qc_statuses(*row), axis=1)
    sum_table.columns = sum_table.columns.str.replace(
        ".all_checks_passed", "", regex=False
    ).str.replace(".qc_status", "", regex=False)
    return sum_table


def make_sample_counts(df):
    sum_table = get_sum_table(df)
    total_samples = len(sum_table)
    pass_count = sum_table["QC"].value_counts().get("PASS", 0)
    warn_count = sum_table["QC"].value_counts().get("WARN", 0)
    fail_count = sum_table["QC"].value_counts().get("FAIL", 0)
    not_evaluated_count = sum_table["QC"].value_counts().get("NOT_EVALUATED", 0)
    pass_percentage = (pass_count / total_samples) * 100 if total_samples > 0 else 0
    return (
        f"There are {total_samples} samples included with "
        f"<span class='qc-pass-text'>{pass_count} passing</span> and "
        f"<span class='qc-warn-text'>{warn_count} warning</span> and "
        f"<span class='qc-fail-text'>{fail_count} failing</span> "
        f"and <span class='qc-not-evaluated-text'>{not_evaluated_count} not evaluated</span> "
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


def build_concise_report_frame(df):
    preferred_columns = [
        ("sample_id", "sample_id"),
        ("overall_qc", "overall_qc"),
        ("speccheck_qc", "speccheck_qc"),
        ("qualibact_qc", "qualibact_qc"),
        ("historical_qualibact_qc", "historical_qualibact_qc"),
        ("reason_summary", "reason_summary"),
        ("species", "species"),
        ("Speciator.speciesName", "species"),
        ("species_confidence", "species_confidence"),
        ("Speciator.confidence", "species_confidence"),
        ("Quast.N50", "n50"),
        ("Checkm.N50 (scaffolds)", "n50"),
        ("Checkm.Contig_N50", "n50"),
        ("Quast.# contigs (>= 0 bp)", "contigs"),
        ("Checkm.# contigs", "contigs"),
        ("Checkm.Total_Contigs", "contigs"),
        ("Quast.Total length (>= 0 bp)", "genome_size"),
        ("Quast.Total length", "genome_size"),
        ("Checkm.Genome size (bp)", "genome_size"),
        ("Checkm.Genome_Size", "genome_size"),
        ("Quast.GC (%)", "gc_percent"),
        ("Checkm.GC", "gc_percent"),
        ("Checkm.GC_Content", "gc_percent"),
        ("Checkm.Completeness", "completeness"),
        ("Checkm.Contamination", "contamination"),
        ("Depth.Depth", "depth"),
        ("Sylph.top_species", "top_species"),
        ("Sylph.top_abundance_percent", "top_abundance_percent"),
        ("Sylph.top_taxonomic_abundance", "top_abundance_percent"),
        ("threshold_source", "threshold_source"),
        ("speccheck_threshold_source", "threshold_source"),
    ]
    data = {}
    for source, target in preferred_columns:
        if source not in df.columns or target in data:
            continue
        data[target] = df[source]
    ordered = [
        "sample_id",
        "overall_qc",
        "speccheck_qc",
        "qualibact_qc",
        "historical_qualibact_qc",
        "reason_summary",
        "species",
        "species_confidence",
        "n50",
        "contigs",
        "genome_size",
        "gc_percent",
        "completeness",
        "contamination",
        "depth",
        "top_species",
        "top_abundance_percent",
        "threshold_source",
        "report_schema_version",
    ]
    concise = pd.DataFrame(data, index=df.index)
    concise["report_schema_version"] = REPORT_SCHEMA_VERSION
    for column in ordered:
        if column not in concise.columns:
            concise[column] = pd.NA
    return concise[ordered]


REPORT_METRIC_ALIASES = {
    "Checkm.GC_Content": ("Checkm.GC",),
    "Checkm.Genome_Size": ("Checkm.Genome size (bp)",),
    "Checkm.Contig_N50": ("Checkm.N50 (scaffolds)",),
    "Checkm.Total_Contigs": ("Checkm.# contigs",),
    "Quast.# contigs (>= 0 bp)": ("Quast.# contigs",),
    "Quast.Total length (>= 0 bp)": ("Quast.Total length",),
}

REPORT_TOOL_ORDER = (
    "Speciator",
    "Depth",
    "Sylph",
    "Quast",
    "Checkm",
    "Fastp",
    "Busco",
    "Ariba",
)


def build_full_report_frame(df):
    """Build a human-first full report with proven-equivalent aliases collapsed."""
    canonical = build_concise_report_frame(df)
    detail = df.copy()

    for target, aliases in REPORT_METRIC_ALIASES.items():
        _validate_equivalent_columns(detail, target, aliases)
        if target not in detail.columns:
            source = next((alias for alias in aliases if alias in detail.columns), None)
            if source is not None:
                detail[target] = detail[source]
        target_status = f"{target}.status"
        status_candidates = [
            f"{target}.check",
            *(f"{alias}.status" for alias in aliases),
            *(f"{alias}.check" for alias in aliases),
        ]
        if target_status not in detail.columns:
            source_status = next(
                (column for column in status_candidates if column in detail.columns),
                None,
            )
            if source_status is not None:
                detail[target_status] = detail[source_status]
        columns_to_drop = [
            column
            for column in (
                *aliases,
                *status_candidates,
            )
            if column in detail.columns
        ]
        detail.drop(columns=columns_to_drop, inplace=True)

    redundant = {
        *canonical.columns,
        "all_checks_passed",
        "baseline_qc",
        "speccheck_overall_status",
        "speccheck_baseline_checks_passed",
        "speccheck_species_checks_passed",
        "speccheck_species_checks_available",
        "speccheck_threshold_source",
        "qualibact_tier",
        "qualibact_compat_tier",
        "qualibact_compat_passed",
        "qualibact_compat_warn_policy",
    }
    redundant.update(column for column in detail.columns if column.endswith(".all_checks_passed"))
    detail.drop(columns=[column for column in redundant if column in detail], inplace=True)

    # Prefer canonical status columns. Legacy *.check columns are retained only
    # when no matching *.status column exists, and are renamed on output.
    for column in list(detail.columns):
        if not column.endswith(".check"):
            continue
        status_column = column.removesuffix(".check") + ".status"
        if status_column in detail.columns:
            detail.drop(columns=[column], inplace=True)
        else:
            detail.rename(columns={column: status_column}, inplace=True)

    ordered = []

    def add_matching(predicate):
        for column in detail.columns:
            if column not in ordered and predicate(column):
                ordered.append(column)

    add_matching(lambda column: column.startswith("speccheck_") and column.endswith("_qc"))
    for tool in REPORT_TOOL_ORDER:
        prefix = f"{tool}."
        add_matching(
            lambda column, prefix=prefix: (
                column.startswith(prefix) and column.endswith(".qc_status")
            )
        )
        metric_columns = [
            column
            for column in detail.columns
            if column.startswith(prefix) and not column.endswith((".qc_status", ".status"))
        ]
        for metric_column in metric_columns:
            if metric_column not in ordered:
                ordered.append(metric_column)
            metric_status = f"{metric_column}.status"
            if metric_status in detail.columns and metric_status not in ordered:
                ordered.append(metric_status)
        add_matching(
            lambda column, prefix=prefix: column.startswith(prefix) and column.endswith(".status")
        )
    add_matching(lambda column: column.startswith("qualibact_compat_"))
    add_matching(lambda column: column.startswith("qualibact_"))
    add_matching(lambda column: column.startswith("speccheck_"))
    add_matching(lambda column: "." not in column)
    add_matching(lambda _column: True)

    return pd.concat([canonical, detail[ordered]], axis=1)


def _validate_equivalent_columns(frame, canonical, aliases):
    """Refuse to collapse aliases when populated values disagree."""
    available = [column for column in (canonical, *aliases) if column in frame.columns]
    for index, left_column in enumerate(available):
        for right_column in available[index + 1 :]:
            left = frame[left_column]
            right = frame[right_column]
            populated = left.notna() & right.notna()
            if not populated.any():
                continue
            left_values = left[populated]
            right_values = right[populated]
            left_numeric = pd.to_numeric(left_values, errors="coerce")
            right_numeric = pd.to_numeric(right_values, errors="coerce")
            both_numeric = left_numeric.notna() & right_numeric.notna()
            equal = pd.Series(False, index=left_values.index)
            equal.loc[both_numeric] = left_numeric[both_numeric].eq(right_numeric[both_numeric])
            equal.loc[~both_numeric] = (
                left_values[~both_numeric].astype(str).str.strip()
                == right_values[~both_numeric].astype(str).str.strip()
            )
            if equal.all():
                continue
            conflicting_rows = [str(value) for value in equal.index[~equal][:5]]
            raise ValueError(
                f"Cannot collapse report aliases '{left_column}' and '{right_column}': "
                f"values differ in row(s) {', '.join(conflicting_rows)}."
            )


def build_large_run_summary_table(df, interactive_tables=True):
    summary_df = build_concise_report_frame(df).copy()
    review_columns = [
        "sample_id",
        "overall_qc",
        "speccheck_qc",
        "qualibact_qc",
        "reason_summary",
        "species",
        "n50",
        "contigs",
    ]
    summary_df = summary_df[[column for column in review_columns if column in summary_df.columns]]
    if "overall_qc" in summary_df.columns:
        ranks = (
            summary_df["overall_qc"]
            .map({"FAIL": 0, "WARN": 1, "NOT_EVALUATED": 2, "PASS": 3})
            .fillna(4)
        )
        summary_df = (
            summary_df.assign(_status_rank=ranks)
            .sort_values(["_status_rank", "sample_id"], kind="stable")
            .drop(columns="_status_rank")
        )
    if "reason_summary" in summary_df.columns:
        summary_df["reason_summary"] = summary_df["reason_summary"].map(_humanize_reason_summary)
    label_map = {
        "sample_id": "Sample",
        "overall_qc": "Overall QC",
        "speccheck_qc": "Speccheck QC",
        "qualibact_qc": "QualiBact QC",
        "historical_qualibact_qc": "Historical QualiBact QC",
        "species": "Species",
        "species_confidence": "Species confidence",
        "n50": "N50",
        "contigs": "Contigs",
        "genome_size": "Genome size",
        "gc_percent": "GC %",
        "completeness": "Completeness",
        "contamination": "Contamination",
        "depth": "Depth",
        "top_species": "Top species",
        "top_abundance_percent": "Top abundance (%)",
        "reason_summary": "Reason summary",
        "threshold_source": "Threshold source",
    }
    summary_df = summary_df.rename(columns=label_map)
    return dataframe_to_interactive_table(
        summary_df,
        table_id="sample-review-table",
        interactive=interactive_tables,
        page_size=25,
        row_status_column="Overall QC",
        row_id_column="Sample",
        clickable_rows=interactive_tables,
    )


def _humanize_reason_summary(value):
    if pd.isna(value):
        return ""
    replacements = {
        "Checkm.": "CheckM: ",
        "Quast.": "QUAST: ",
        "Speciator.": "Speciator: ",
        "Sylph.": "Sylph: ",
        "GC_Content": "GC content",
        "Genome_Size": "genome size",
        "Contig_N50": "N50",
        "Total_Contigs": "contig count",
        "speciesName": "species assignment",
        "genusName": "genus assignment",
        "no_of_contigs": "contig count",
        "Total_Coding_Sequences": "coding sequence count",
        "Completeness_Specific": "completeness",
    }
    readable = str(value)
    for source, target in replacements.items():
        readable = readable.replace(source, target)
    return readable


def build_full_detail_table(df, interactive_tables=True):
    return dataframe_to_interactive_table(
        df,
        table_id="full-detail-table",
        interactive=interactive_tables,
        page_size=25,
    )


def get_failure_reasons(df, software_dict):
    sum_table = get_sum_table(df)
    failure_columns = [
        column for column in sum_table.columns if column not in {"QC", "all_checks_passed"}
    ]
    failure_reasons = sum_table[sum_table["QC"] == "FAIL"][failure_columns].apply(
        lambda series: series == "FAIL"
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
                    "qualibact_qc",
                    "historical_qualibact_qc",
                    "Sylph.top_species",
                    "Sylph.top_abundance_percent",
                    "Sylph.top_taxonomic_abundance",
                ],
            ),
            (
                "Assembly quality",
                [
                    "Quast.N50",
                    "Quast.# contigs (>= 0 bp)",
                    "Quast.Total length (>= 0 bp)",
                    "Quast.GC (%)",
                    "Quast.Largest contig",
                ],
            ),
            (
                "Completeness and contamination",
                [
                    "Checkm.Completeness",
                    "Checkm.Contamination",
                    "Checkm.GC_Content",
                    "Checkm.Genome_Size",
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


def build_species_metric_summary_frames(df):
    """Build metric summaries for each reported species in a mixed cohort."""
    species_column = next(
        (column for column in ("species", "Speciator.speciesName") if column in df),
        None,
    )
    if species_column is None:
        return OrderedDict()

    species = df[species_column].fillna("Not assigned").astype(str).str.strip()
    species = species.mask(species.str.lower().isin({"", "nan", "none"}), "Not assigned")
    counts = species.value_counts()
    if len(counts) <= 1:
        return OrderedDict()

    summaries = OrderedDict()
    for species_name, count in counts.items():
        summaries[species_name] = (
            int(count),
            build_metric_summary_frames(df.loc[species == species_name]),
        )
    return summaries


def _render_metric_summary_grid(summary_frames, table_id_prefix):
    sections = ['<section class="metric-summary-grid">']
    for index, (category, frame) in enumerate(summary_frames.items(), start=1):
        sections.append(
            '<article class="metric-summary-card">'
            f"<h3>{escape(category)}</h3>"
            f"{dataframe_to_interactive_table(frame, f'{table_id_prefix}-{index}', searchable=False, interactive=False)}"
            "</article>"
        )
    sections.append("</section>")
    return "".join(sections)


def render_metric_summary_tables(
    summary_frames,
    qualifyr_style=False,
    interactive_tables=True,
    species_summary_frames=None,
):
    if not summary_frames:
        return ""
    intro = "<p>Compact summary tables give a quick view of key QC metrics across the dataset.</p>"
    if qualifyr_style:
        intro = (
            "<p>Compact summary tables are rendered in a built-in qualifyr-style layout "
            "for quick comparison across samples.</p>"
        )
    overall_grid = _render_metric_summary_grid(summary_frames, "metric-summary-all")
    if not interactive_tables or not species_summary_frames:
        return intro + overall_grid

    total = sum(count for count, _frames in species_summary_frames.values())
    options = [
        f'<option value="all" data-sample-count="{total}">All species ({total} samples)</option>'
    ]
    views = [f'<div class="metric-summary-view" data-metric-species="all">{overall_grid}</div>']
    for index, (species_name, (count, frames)) in enumerate(
        species_summary_frames.items(), start=1
    ):
        token = f"species-{index}"
        options.append(
            f'<option value="{token}" data-sample-count="{count}">'
            f"{escape(species_name)} ({count} sample{'s' if count != 1 else ''})</option>"
        )
        views.append(
            f'<div class="metric-summary-view" data-metric-species="{token}" hidden>'
            f"{_render_metric_summary_grid(frames, f'metric-summary-{token}')}</div>"
        )
    controls = (
        '<div class="metric-species-filter">'
        '<label for="metric-species-filter">View cohort metrics for</label>'
        f'<select id="metric-species-filter">{"".join(options)}</select>'
        f'<p id="metric-species-summary" aria-live="polite">Showing all {total} samples.</p>'
        "</div>"
    )
    return intro + controls + "".join(views)


def export_summary_workbook(summary_df, full_df, output_path, summary_frames):
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        summary_df.to_excel(writer, sheet_name="report", index=False)
        full_df.to_excel(writer, sheet_name="full", index=False)
        get_sum_table(full_df.set_index("sample_id")).reset_index().rename(
            columns={"index": "sample_id"}
        ).to_excel(writer, sheet_name="qc_status", index=False)
        for sheet_index, (category, frame) in enumerate(summary_frames.items(), start=1):
            safe_name = category[:31] if len(category) <= 31 else category[:28] + "..."
            frame.to_excel(writer, sheet_name=safe_name or f"sheet{sheet_index}", index=False)


def build_qualifyr_style_table(df, interactive_tables=True):
    preferred_columns = [
        "sample_id",
        "overall_qc",
        "speccheck_qc",
        "qualibact_qc",
        "historical_qualibact_qc",
        "Speciator.speciesName",
        "Speciator.confidence",
        "Quast.N50",
        "Quast.# contigs (>= 0 bp)",
        "Quast.Total length (>= 0 bp)",
        "Checkm.Completeness",
        "Checkm.Contamination",
        "qualibact_compat_reasons",
        "qualibact_reasons",
    ]
    available_columns = [column for column in preferred_columns if column in df.columns]
    if not available_columns:
        return ""
    qualifyr_df = df[available_columns].copy()
    html = "<p>This compact table uses a qualifyr-like layout for fast sample review.</p>"
    return html + dataframe_to_interactive_table(
        qualifyr_df, "qualifyr-style-table", interactive=interactive_tables
    )
