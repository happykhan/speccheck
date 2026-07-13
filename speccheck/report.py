import logging
from pathlib import Path

import pandas as pd
from jinja2 import Template

from speccheck import __version__ as VERSION
from speccheck.registry import PLOT_CLASSES, add_frame_metric_aliases
from speccheck.report_tables import (
    build_concise_report_frame,
    build_full_detail_table,
    build_large_run_summary_table,
    build_metric_summary_frames,
    build_qualifyr_style_table,
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
    plotly_jinja_data = {"software_charts": ""}
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
        software_dict[software] = software_obj.summary()
        plotly_jinja_data["software_charts"] += software_obj.plot()

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
    plotly_jinja_data["sample_count"] = make_sample_counts(report_df.set_index("sample_id"))
    plotly_jinja_data["footer"] = make_footer()
    plotly_jinja_data["summary_table"] = summary_table(
        report_df.set_index("sample_id"),
        interactive_tables=interactive_tables,
    )
    plotly_jinja_data["dataset_kpis"] = _build_dataset_kpis(report_df)
    plotly_jinja_data["run_alerts"] = _build_run_alerts(concise_report_df)
    plotly_jinja_data["sample_review_table"] = build_large_run_summary_table(
        report_df,
        interactive_tables=interactive_tables,
    )
    plotly_jinja_data["full_detail_table"] = build_full_detail_table(
        report_df,
        interactive_tables=interactive_tables,
    )
    plotly_jinja_data["software_summary"] = get_software_summary(software_dict)
    plotly_jinja_data["failure_reasons"] = get_failure_reasons(
        report_df.set_index("sample_id"), software_dict
    )
    plotly_jinja_data["metric_summary_tables"] = render_metric_summary_tables(
        summary_frames,
        qualifyr_style=qualifyr_style,
        interactive_tables=interactive_tables,
    )
    plotly_jinja_data["qualifyr_style_table"] = (
        build_qualifyr_style_table(report_df, interactive_tables=interactive_tables)
        if qualifyr_style
        else ""
    )
    plotly_jinja_data["interactive_tables"] = interactive_tables
    plotly_jinja_data["version"] = VERSION
    return plotly_jinja_data, report_df, summary_frames


def plot_charts(
    merged_dict,
    species,
    output_html_path="report.html",
    input_template_path=None,
    interactive_tables=True,
    qualifyr_style=False,
):
    template_path = Path(input_template_path or get_default_template_path())
    plotly_jinja_data, report_df, summary_frames = build_report_context(
        merged_dict,
        species,
        interactive_tables=interactive_tables,
        qualifyr_style=qualifyr_style,
    )
    plotly_jinja_data["embedded_styles"] = get_embedded_report_styles(template_path)
    required_keys = [
        "software_charts",
        "summary_table",
        "dataset_kpis",
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
        if key not in plotly_jinja_data:
            logging.error("Missing required key in plotly_jinja_data: %s", key)
            return None
    with open(output_html_path, "w", encoding="utf-8") as output_file:
        with open(template_path, encoding="utf-8") as template_file:
            j2_template = Template(template_file.read())
            output_file.write(j2_template.render(plotly_jinja_data))
    return report_df, summary_frames


def _build_dataset_kpis(report_df):
    total = len(report_df)
    if total == 0:
        return []
    overall = report_df.get("overall_qc", report_df.get("all_checks_passed", pd.Series(dtype=object)))
    labels = overall.map(status_label).replace({"PASSED": "PASS", "FAILED": "FAIL"})
    pass_count = int((labels == "PASS").sum())
    warn_count = int((labels == "WARN").sum())
    fail_count = int((labels == "FAIL").sum())
    pass_rate = (pass_count / total) * 100
    threshold_source = "Unavailable"
    if "threshold_source" in report_df.columns and report_df["threshold_source"].notna().any():
        threshold_source = str(report_df["threshold_source"].dropna().iloc[0])
    species_summary = "Species unavailable"
    if "species" in report_df.columns and report_df["species"].notna().any():
        counts = report_df["species"].fillna("Unknown").value_counts()
        if len(counts) == 1:
            species_summary = counts.index[0]
        else:
            species_summary = f"{len(counts)} species; dominant {counts.index[0]} ({counts.iloc[0]})"
    return [
        {"label": "Samples", "value": total, "tone": "neutral"},
        {"label": "PASS", "value": pass_count, "tone": "pass"},
        {"label": "WARN", "value": warn_count, "tone": "warn"},
        {"label": "FAIL", "value": fail_count, "tone": "fail"},
        {"label": "Pass rate", "value": f"{pass_rate:.1f}%", "tone": "neutral"},
        {"label": "Threshold source", "value": threshold_source, "tone": "neutral"},
        {"label": "Species mix", "value": species_summary, "tone": "neutral"},
    ]


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
            counts[part] = counts.get(part, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"reason": reason, "count": count} for reason, count in ranked[:8]]
