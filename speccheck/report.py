import json
import logging
from html import escape
from pathlib import Path

import pandas as pd
from jinja2 import Template

from speccheck import __version__ as VERSION
from speccheck.registry import PLOT_CLASSES, add_frame_metric_aliases
from speccheck.report_tables import (
    build_concise_report_frame,
    build_full_detail_table,
    build_full_report_frame,
    build_large_run_summary_table,
    build_metric_summary_frames,
    build_qualifyr_style_table,
    build_species_metric_summary_frames,
    combine_qc_statuses,
    format_numeric,
    get_failure_reasons,
    make_sample_counts,
    normalize_status,
    render_metric_summary_tables,
    safe_anchor,
    status_label,
    summary_table,
)

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
DEFAULT_TEMPLATE_PATH = TEMPLATE_DIR / "report.html"
DEFAULT_STYLE_PATH = TEMPLATE_DIR / "report.css"


def get_default_template_path():
    return str(DEFAULT_TEMPLATE_PATH)


def get_default_style_path():
    return str(DEFAULT_STYLE_PATH)


def get_embedded_report_styles(template_path=None):
    style_path = DEFAULT_STYLE_PATH
    if template_path is not None:
        candidate = Path(template_path).with_name("report.css")
        if candidate.exists():
            style_path = candidate
    return style_path.read_text(encoding="utf-8")


def make_footer():
    return (
        f'<p>Produced with <a href="https://github.com/happykhan/speccheck">speccheck</a> '
        f"version {VERSION}</p>"
    )


def load_modules_with_checks():
    """Return the explicitly supported plotting classes."""
    module_dict = dict(PLOT_CLASSES)
    loaded_classes = ", ".join(cls.__name__ for cls in module_dict.values())
    logging.debug("Loaded modules: %s", loaded_classes)
    return module_dict


def get_software_summary(software_dict):
    if not software_dict:
        return "<p>No plotting modules were available for the detected software.</p>"
    summary = "<p>Software included in this report:</p><ul>"
    for soft in software_dict.values():
        summary += (
            f'<li><b><a href="#{safe_anchor(soft["name"])}">{soft["name"]}</a></b>: '
            f"{soft['description']}"
        )
        if soft.get("url"):
            summary += f' (<a href="{soft["url"]}">website</a>)'
        if soft.get("version"):
            summary += f" (version: {soft['version']})"
        if soft.get("citation"):
            summary += f' (<a href="{soft["citation"]}">ref</a>)'
        summary += "</li>"
    return summary + "</ul>"


def build_report_context(
    merged_dict,
    species,
    interactive_tables=True,
    qualifyr_style=False,
):
    software_modules = load_modules_with_checks()
    report_context = {"software_charts": "", "software_navigation": []}
    for idx, (key, value) in enumerate(merged_dict.items(), start=1):
        if not isinstance(value, dict):
            merged_dict[key] = {}
        if "sample_id" not in merged_dict[key] or pd.isna(merged_dict[key]["sample_id"]):
            merged_dict[key]["sample_id"] = f"sample{idx}"

    df = pd.DataFrame.from_dict(merged_dict, orient="index")
    if "all_checks_passed" in df.columns:
        overall_status = df["all_checks_passed"].copy()
        df.drop(columns=["all_checks_passed"], inplace=True)
    else:
        overall_status = None

    if species not in df.columns:
        df[species] = "Unknown"

    software_dict = {}
    groups = df.columns.to_series().str.split(".").str[0]
    unique_groups = [group for group in groups.unique() if group in software_modules]
    for software in unique_groups:
        group_df = df[[col for col in df.columns if col.startswith(software)]].copy()
        group_df = group_df.join(df[species].rename("species"))
        group_df = group_df.join(df["sample_id"].rename("sample_id"))
        group_df.columns = group_df.columns.str.replace(f"{software}.", "", regex=False)
        group_df.index = group_df["sample_id"]
        group_df.attrs["interactive_tables"] = interactive_tables
        group_df = add_frame_metric_aliases(group_df, software)
        software_obj = software_modules[software](group_df)
        software_summary = software_obj.summary()
        software_dict[software] = software_summary
        counts = _status_counts(group_df)
        tool_id = f"tool-{safe_anchor(software_summary['name'])}"
        report_context["software_navigation"].append(
            {
                "id": tool_id,
                "name": software_summary["name"],
                "review_count": counts["FAIL"] + counts["WARN"] + counts["NOT_EVALUATED"],
            }
        )
        report_context["software_charts"] += (
            f'<details class="tool-diagnostic" id="{tool_id}">'
            '<summary class="tool-diagnostic-summary">'
            '<span class="tool-summary-copy">'
            f'<span class="tool-name">{escape(software_summary["name"])}</span>'
            f'<span class="tool-description">{escape(software_summary["description"])}</span>'
            "</span>"
            f'<span class="tool-status-badges">{_status_badges(counts)}</span>'
            "</summary>"
            f'<div class="tool-diagnostic-body">{software_obj.plot()}</div>'
            "</details>"
        )

    report_df = df.copy()
    if overall_status is not None:
        report_df["all_checks_passed"] = overall_status
    else:
        report_df["all_checks_passed"] = report_df.apply(
            lambda row: all(
                normalize_status(value) is not False
                for column, value in row.items()
                if column.endswith("all_checks_passed")
            ),
            axis=1,
        )
    report_df = report_df.reset_index(drop=True)

    summary_frames = build_metric_summary_frames(report_df)
    concise_report_df = build_concise_report_frame(report_df)
    report_context["sample_count"] = make_sample_counts(report_df.set_index("sample_id"))
    report_context["footer"] = make_footer()
    report_context["summary_table"] = summary_table(
        report_df.set_index("sample_id"),
        interactive_tables=interactive_tables,
    )
    report_context["dataset_kpis"] = _build_dataset_kpis(report_df)
    report_context["review_status_counts"] = _build_review_status_counts(report_df)
    report_context["sample_details_json"] = _build_sample_details_json(report_df)
    report_context["run_context"] = _build_run_context(report_df)
    report_context["run_alerts"] = _build_run_alerts(concise_report_df)
    report_context["sample_review_table"] = build_large_run_summary_table(
        report_df,
        interactive_tables=interactive_tables,
    )
    report_context["full_detail_table"] = build_full_detail_table(
        build_full_report_frame(report_df),
        interactive_tables=interactive_tables,
    )
    report_context["software_summary"] = get_software_summary(software_dict)
    report_context["failure_reasons"] = get_failure_reasons(
        report_df.set_index("sample_id"), software_dict
    )
    report_context["metric_summary_tables"] = render_metric_summary_tables(
        summary_frames,
        qualifyr_style=qualifyr_style,
        interactive_tables=interactive_tables,
        species_summary_frames=build_species_metric_summary_frames(report_df),
    )
    report_context["qualifyr_style_table"] = (
        build_qualifyr_style_table(report_df, interactive_tables=interactive_tables)
        if qualifyr_style
        else ""
    )
    report_context["interactive_tables"] = interactive_tables
    report_context["version"] = VERSION
    return report_context, report_df, summary_frames


def plot_charts(
    merged_dict,
    species,
    output_html_path="report.html",
    input_template_path=None,
    interactive_tables=True,
    qualifyr_style=False,
):
    template_path = Path(input_template_path or get_default_template_path())
    report_context, report_df, summary_frames = build_report_context(
        merged_dict,
        species,
        interactive_tables=interactive_tables,
        qualifyr_style=qualifyr_style,
    )
    report_context["embedded_styles"] = get_embedded_report_styles(template_path)
    required_keys = [
        "software_charts",
        "software_navigation",
        "summary_table",
        "dataset_kpis",
        "review_status_counts",
        "sample_details_json",
        "run_context",
        "run_alerts",
        "sample_review_table",
        "full_detail_table",
        "footer",
        "sample_count",
        "software_summary",
        "failure_reasons",
        "interactive_tables",
        "metric_summary_tables",
        "qualifyr_style_table",
        "version",
        "embedded_styles",
    ]
    for key in required_keys:
        if key not in report_context:
            logging.error("Missing required key in report context: %s", key)
            return None
    with open(output_html_path, "w", encoding="utf-8") as output_file:
        with open(template_path, encoding="utf-8") as template_file:
            j2_template = Template(template_file.read())
            output_file.write(j2_template.render(report_context))
    return report_df, summary_frames


def _build_dataset_kpis(report_df):
    total = len(report_df)
    if total == 0:
        return []
    overall = report_df.get(
        "overall_qc", report_df.get("all_checks_passed", pd.Series(dtype=object))
    )
    labels = overall.map(status_label)
    pass_count = int((labels == "PASS").sum())
    warn_count = int((labels == "WARN").sum())
    fail_count = int((labels == "FAIL").sum())
    pass_rate = (pass_count / total) * 100
    not_evaluated_count = int((labels == "NOT_EVALUATED").sum())
    return [
        {"label": "Samples", "value": total, "tone": "neutral", "filter": "ALL"},
        {"label": "PASS", "value": pass_count, "tone": "pass", "filter": "PASS"},
        {"label": "WARN", "value": warn_count, "tone": "warn", "filter": "WARN"},
        {"label": "FAIL", "value": fail_count, "tone": "fail", "filter": "FAIL"},
        {
            "label": "NOT EVALUATED",
            "value": not_evaluated_count,
            "tone": "not-evaluated",
            "filter": "NOT_EVALUATED",
        },
        {"label": "Pass rate", "value": f"{pass_rate:.1f}%", "tone": "neutral"},
    ]


def _build_run_context(report_df):
    context = []
    if "species" in report_df.columns and report_df["species"].notna().any():
        counts = report_df["species"].fillna("Unknown").value_counts()
        species_summary = str(counts.index[0])
        if len(counts) > 1:
            species_summary = f"{len(counts)} calls; dominant {counts.index[0]} ({counts.iloc[0]})"
        context.append({"label": "Species", "value": escape(species_summary)})
    if "threshold_source" in report_df.columns and report_df["threshold_source"].notna().any():
        sources = report_df["threshold_source"].dropna().astype(str).unique()
        value = sources[0] if len(sources) == 1 else f"{len(sources)} threshold sources"
        context.append({"label": "Thresholds", "value": escape(value)})
    if "qualibact_qc" in report_df.columns:
        labels = report_df["qualibact_qc"].map(status_label)
        not_evaluated = int((labels == "NOT_EVALUATED").sum())
        if not_evaluated:
            evaluated = len(labels) - not_evaluated
            context.append(
                {
                    "label": "QualiBact",
                    "value": f"{evaluated}/{len(labels)} evaluated; {not_evaluated} not evaluated",
                }
            )
    return context


def _status_counts(frame):
    counts = dict.fromkeys(("PASS", "WARN", "FAIL", "NOT_EVALUATED"), 0)
    if "qc_status" in frame.columns:
        labels = frame["qc_status"].map(status_label)
    elif "all_checks_passed" in frame.columns:
        labels = frame["all_checks_passed"].map(status_label)
    else:
        status_columns = [
            column for column in frame.columns if column.endswith((".status", ".check"))
        ]
        if not status_columns:
            return counts
        labels = frame[status_columns].apply(lambda row: combine_qc_statuses(*row.tolist()), axis=1)
    for status in counts:
        counts[status] = int((labels == status).sum())
    return counts


def _status_badges(counts):
    labels = []
    for status, css_class in (
        ("FAIL", "fail"),
        ("WARN", "warn"),
        ("NOT_EVALUATED", "not-evaluated"),
        ("PASS", "pass"),
    ):
        count = counts[status]
        if count:
            visible_status = "NOT EVALUATED" if status == "NOT_EVALUATED" else status
            labels.append(
                f'<span class="status-badge status-badge-{css_class}">{count} {visible_status}</span>'
            )
    return "".join(labels) or '<span class="status-badge">No status</span>'


def _build_review_status_counts(report_df):
    overall = report_df.get(
        "overall_qc", report_df.get("all_checks_passed", pd.Series(dtype=object))
    ).map(status_label)
    counts = {
        status: int((overall == status).sum())
        for status in ("FAIL", "WARN", "NOT_EVALUATED", "PASS")
    }
    counts["NEEDS_REVIEW"] = counts["FAIL"] + counts["WARN"] + counts["NOT_EVALUATED"]
    counts["ALL"] = len(report_df)
    return counts


def _display_report_value(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)):
        return format_numeric(value)
    label = status_label(value)
    return label or str(value)


def _build_sample_details_json(report_df):
    concise = build_concise_report_frame(report_df)
    tool_status_columns = [column for column in report_df.columns if column.endswith(".qc_status")]
    check_status_columns = [column for column in report_df.columns if column.endswith(".status")]
    details = {}
    for index, concise_row in concise.iterrows():
        sample_id = str(concise_row["sample_id"])
        source_row = report_df.loc[index]
        overview_fields = [
            ("Overall QC", concise_row["overall_qc"]),
            ("Speccheck QC", concise_row["speccheck_qc"]),
            ("QualiBact QC", concise_row["qualibact_qc"]),
            ("Historical QualiBact QC", concise_row["historical_qualibact_qc"]),
            ("Species", concise_row["species"]),
            ("Species confidence", concise_row["species_confidence"]),
            ("Reason", concise_row["reason_summary"]),
        ]
        metric_fields = [
            ("N50", concise_row["n50"]),
            ("Contigs", concise_row["contigs"]),
            ("Genome size", concise_row["genome_size"]),
            ("GC (%)", concise_row["gc_percent"]),
            ("Completeness", concise_row["completeness"]),
            ("Contamination", concise_row["contamination"]),
            ("Depth", concise_row["depth"]),
            ("Top species", concise_row["top_species"]),
            ("Top abundance (%)", concise_row["top_abundance_percent"]),
        ]
        tool_fields = [
            (column.removesuffix(".qc_status"), source_row[column])
            for column in tool_status_columns
            if not pd.isna(source_row[column])
        ]
        check_fields = []
        for column in check_status_columns:
            check_status = status_label(source_row[column])
            if check_status in {"", "PASS"}:
                continue
            metric_column = column.removesuffix(".status")
            metric_value = source_row.get(metric_column, "")
            value = check_status
            if not pd.isna(metric_value) and str(metric_value) != "":
                value = f"{check_status} ({_display_report_value(metric_value)})"
            check_fields.append((metric_column, value))
        provenance_fields = [
            ("Threshold source", concise_row["threshold_source"]),
            ("QualiBact threshold source", source_row.get("qualibact_compat_source", "")),
            ("Report schema", concise_row["report_schema_version"]),
        ]

        def clean(fields):
            return [
                {"label": label, "value": _display_report_value(value)}
                for label, value in fields
                if not pd.isna(value) and str(value).strip() not in {"", "nan", "none"}
            ]

        details[sample_id] = {
            "overview": clean(overview_fields),
            "metrics": clean(metric_fields),
            "tools": clean(tool_fields),
            "checks": clean(check_fields),
            "provenance": clean(provenance_fields),
        }
    return json.dumps(details, ensure_ascii=False).replace("</", "<\\/")


def _build_run_alerts(concise_report_df):
    if concise_report_df.empty or "reason_summary" not in concise_report_df.columns:
        return []
    alerts = (
        concise_report_df[concise_report_df["overall_qc"].isin(["WARN", "FAIL"])]["reason_summary"]
        .fillna("none")
        .astype(str)
    )
    counts = {}
    for value in alerts:
        if not value or value.lower() == "none":
            continue
        for part in [item.strip() for item in value.split(";") if item.strip()]:
            readable = _humanize_reason(part)
            counts[readable] = counts.get(readable, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"reason": reason, "count": count} for reason, count in ranked[:8]]


def _humanize_reason(reason):
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
    }
    readable = str(reason)
    for source, target in replacements.items():
        readable = readable.replace(source, target)
    return escape(readable)
