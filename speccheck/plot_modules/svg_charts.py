"""Small, dependency-free SVG charts for the standalone HTML report."""

from __future__ import annotations

from html import escape
from math import isfinite

import pandas as pd

from speccheck.report_tables import status_label

STATUS_COLOURS = {
    "PASS": "#2b7a4b",
    "WARN": "#a06f00",
    "FAIL": "#b64242",
    "NOT_EVALUATED": "#66778a",
}
STATUS_ORDER = ("PASS", "WARN", "FAIL", "NOT_EVALUATED")


def _format_tick(value: float) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.0f}k"
    if absolute >= 10:
        return f"{value:.0f}"
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _domain(values: pd.Series) -> tuple[float, float]:
    minimum = float(values.min())
    maximum = float(values.max())
    if minimum == maximum:
        padding = abs(minimum) * 0.08 or 1.0
    else:
        padding = (maximum - minimum) * 0.06
    return minimum - padding, maximum + padding


def _scale(value: float, start: float, end: float, low: float, high: float) -> float:
    return low + ((value - start) / (end - start)) * (high - low)


def _status_series(frame: pd.DataFrame) -> pd.Series:
    if "qc_status" in frame:
        return frame["qc_status"].map(status_label)
    if "all_checks_passed" in frame:
        return frame["all_checks_passed"].map(status_label)
    return pd.Series("NOT_EVALUATED", index=frame.index)


def _status_legend(status_counts: pd.Series) -> str:
    counts = {status: int(status_counts.get(status, 0)) for status in STATUS_ORDER}
    items = "".join(
        '<span><i class="legend-marker '
        f'legend-{status.lower().replace("_", "-")}"></i>'
        f"<strong>{count}</strong> {status.replace('_', ' ')}</span>"
        for status, count in counts.items()
    )
    return (
        '<div class="svg-chart-legend" aria-label="QC status legend">'
        '<span class="legend-heading">QC status</span>'
        f"{items}</div>"
    )


def render_species_bar_chart(
    counts: pd.Series,
    *,
    title: str,
    status_counts: pd.DataFrame | None = None,
) -> str:
    """Render a compact horizontal species-count bar chart, segmented by QC."""
    clean_counts = counts.dropna().astype(int).sort_values(ascending=False)
    if clean_counts.empty:
        return '<p class="chart-empty">No species distribution was available.</p>'

    if status_counts is None:
        status_counts = pd.DataFrame({"NOT_EVALUATED": clean_counts}, index=clean_counts.index)
    else:
        status_counts = status_counts.copy()
        status_counts.columns = [status_label(column) for column in status_counts.columns]
        status_counts = status_counts.T.groupby(level=0).sum().T
        status_counts = status_counts.reindex(clean_counts.index, fill_value=0)
    status_counts = status_counts.reindex(columns=STATUS_ORDER, fill_value=0).fillna(0)
    cohort_status_counts = status_counts.sum(axis=0)

    width = 760
    left = 210
    right = 58
    top = 48
    row_height = 42
    bottom = 28
    height = top + (len(clean_counts) * row_height) + bottom
    plot_width = width - left - right
    maximum = int(clean_counts.max()) or 1
    elements = [
        f'<h3 class="chart-title">{escape(title)}</h3>',
        '<div class="chart-frame inline-chart-frame">',
        _status_legend(cohort_status_counts),
        f'<svg class="inline-svg-chart species-bar-chart" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="species-chart-title species-chart-desc">',
        f'<title id="species-chart-title">{escape(title)}</title>',
        '<desc id="species-chart-desc">Horizontal stacked bars show the number of samples assigned to each species, coloured by QC status.</desc>',
    ]
    for index, (species, count) in enumerate(clean_counts.items()):
        y = top + (index * row_height)
        bar_width = max(2, (int(count) / maximum) * plot_width)
        full_label = str(species)
        display_label = full_label if len(full_label) <= 25 else full_label[:22] + "..."
        elements.append(
            f'<text class="svg-axis-label svg-category-label" x="{left - 12}" y="{y + 20}" '
            f'text-anchor="end">{escape(display_label)}<title>{escape(full_label)}</title></text>'
        )
        segment_x = float(left)
        species_statuses = status_counts.loc[species]
        for status in STATUS_ORDER:
            segment_count = int(species_statuses.get(status, 0))
            if segment_count <= 0:
                continue
            segment_width = (segment_count / maximum) * plot_width
            tooltip = f"{full_label} | {status}: {segment_count} sample(s)"
            status_class = status.lower().replace("_", "-")
            elements.append(
                f'<rect class="svg-bar qc-bar-{status_class}" x="{segment_x:.2f}" '
                f'y="{y + 4}" width="{segment_width:.2f}" height="24" '
                f'fill="{STATUS_COLOURS[status]}" data-tooltip="{escape(tooltip)}">'
                f"<title>{escape(tooltip)}</title></rect>"
            )
            segment_x += segment_width
        elements.append(
            f'<text class="svg-value-label" x="{left + bar_width + 8:.2f}" '
            f'y="{y + 21}">{int(count)}</text>'
        )
    elements.extend(["</svg>", "</div>"])
    return "".join(elements)


def render_scatter_chart(
    frame: pd.DataFrame,
    *,
    x_column: str,
    y_column: str,
    x_label: str,
    y_label: str,
    title: str,
) -> str:
    """Render a QC-coloured scatter chart with accessible sample points."""
    required = [x_column, y_column]
    if any(column not in frame for column in required):
        return '<p class="chart-empty">The metrics required for this chart were unavailable.</p>'

    numeric = pd.DataFrame(
        {
            "x": pd.to_numeric(frame[x_column], errors="coerce"),
            "y": pd.to_numeric(frame[y_column], errors="coerce"),
            "status": _status_series(frame),
            "species": frame.get("species", pd.Series("", index=frame.index)),
            "sample_id": frame.get(
                "sample_id", pd.Series(frame.index.astype(str), index=frame.index)
            ),
        },
        index=frame.index,
    ).dropna(subset=["x", "y"])
    numeric = numeric[
        numeric["x"].map(lambda value: isfinite(float(value)))
        & numeric["y"].map(lambda value: isfinite(float(value)))
    ]
    if numeric.empty:
        return '<p class="chart-empty">No finite values were available for this chart.</p>'

    width = 760
    height = 440
    left = 78
    right = 30
    top = 34
    bottom = 64
    plot_left = left
    plot_right = width - right
    plot_top = top
    plot_bottom = height - bottom
    x_min, x_max = _domain(numeric["x"])
    y_min, y_max = _domain(numeric["y"])
    tick_count = 5
    elements = [
        f'<h3 class="chart-title">{escape(title)}</h3>',
        '<div class="chart-frame inline-chart-frame">',
        f'<svg class="inline-svg-chart scatter-chart" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{escape(title)}">',
        f'<rect class="svg-plot-background" x="{plot_left}" y="{plot_top}" '
        f'width="{plot_right - plot_left}" height="{plot_bottom - plot_top}" />',
    ]
    for tick in range(tick_count + 1):
        fraction = tick / tick_count
        x = plot_left + fraction * (plot_right - plot_left)
        y = plot_bottom - fraction * (plot_bottom - plot_top)
        x_value = x_min + fraction * (x_max - x_min)
        y_value = y_min + fraction * (y_max - y_min)
        elements.extend(
            [
                f'<line class="svg-grid-line" x1="{x:.2f}" y1="{plot_top}" x2="{x:.2f}" y2="{plot_bottom}" />',
                f'<text class="svg-tick-label" x="{x:.2f}" y="{plot_bottom + 22}" text-anchor="middle">{escape(_format_tick(x_value))}</text>',
                f'<line class="svg-grid-line" x1="{plot_left}" y1="{y:.2f}" x2="{plot_right}" y2="{y:.2f}" />',
                f'<text class="svg-tick-label" x="{plot_left - 12}" y="{y + 4:.2f}" text-anchor="end">{escape(_format_tick(y_value))}</text>',
            ]
        )

    status_order = {"PASS": 0, "NOT_EVALUATED": 1, "WARN": 2, "FAIL": 3}
    numeric = numeric.assign(
        _status_order=numeric["status"].map(status_order).fillna(1)
    ).sort_values("_status_order", kind="stable")
    for _, row in numeric.iterrows():
        sample_id = str(row["sample_id"])
        status = row["status"] or "NOT_EVALUATED"
        species = str(row["species"]) if pd.notna(row["species"]) else ""
        x = _scale(float(row["x"]), x_min, x_max, plot_left, plot_right)
        y = _scale(float(row["y"]), y_min, y_max, plot_bottom, plot_top)
        tooltip_parts = [
            sample_id,
            f"{x_label}: {_format_tick(float(row['x']))}",
            f"{y_label}: {_format_tick(float(row['y']))}",
            f"QC: {status}",
        ]
        if species and species.lower() != "nan":
            tooltip_parts.insert(1, species)
        tooltip = " | ".join(tooltip_parts)
        colour = STATUS_COLOURS.get(status, STATUS_COLOURS["NOT_EVALUATED"])
        status_class = status.lower().replace("_", "-")
        attributes = (
            f'class="svg-data-point qc-point-{status_class}" '
            f'fill="{colour}" data-qc-status="{status}" '
            f'data-sample-id="{escape(sample_id)}" data-tooltip="{escape(tooltip)}" '
            f'tabindex="0" role="button" aria-label="{escape(tooltip)}"'
        )
        if status == "PASS":
            point = f'<circle {attributes} cx="{x:.2f}" cy="{y:.2f}" r="5.5"'
            closing_tag = "circle"
        elif status == "WARN":
            point = (
                f'<polygon {attributes} points="{x:.2f},{y - 7:.2f} '
                f'{x + 6.5:.2f},{y + 5.5:.2f} {x - 6.5:.2f},{y + 5.5:.2f}"'
            )
            closing_tag = "polygon"
        elif status == "FAIL":
            point = (
                f'<polygon {attributes} points="{x:.2f},{y - 7:.2f} '
                f'{x + 7:.2f},{y:.2f} {x:.2f},{y + 7:.2f} {x - 7:.2f},{y:.2f}"'
            )
            closing_tag = "polygon"
        else:
            point = f'<rect {attributes} x="{x - 6:.2f}" y="{y - 6:.2f}" width="12" height="12"'
            closing_tag = "rect"
        elements.append(f"{point}><title>{escape(tooltip)}</title></{closing_tag}>")

    elements.extend(
        [
            f'<text class="svg-axis-title" x="{(plot_left + plot_right) / 2:.2f}" y="{height - 14}" text-anchor="middle">{escape(x_label)}</text>',
            f'<text class="svg-axis-title" transform="translate(18 {(plot_top + plot_bottom) / 2:.2f}) rotate(-90)" text-anchor="middle">{escape(y_label)}</text>',
            "</svg>",
            '<p class="chart-help">Colour and shape indicate QC status. Hover for values. Select a point to open the sample details.</p>',
            "</div>",
        ]
    )
    elements.insert(2, _status_legend(numeric["status"].value_counts()))
    return "".join(elements)
