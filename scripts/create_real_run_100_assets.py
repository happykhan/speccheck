#!/usr/bin/env python3
"""Create deterministic worked-example assets for the real 100-sample cohort."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
from collections import Counter
from functools import partial
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = ROOT / ".demo_work/ghru_ecoli_cohort/run_100"
DEFAULT_REPORT_ROOT = ROOT / ".demo_work/publication_100_final/report"
DEFAULT_OUTPUT = ROOT / "examples/qualibact_ecoli/real_run_100"
DOC_FIGURE_DIR = ROOT / "docs/assets/figures"
TIERS = ("PASS", "WARN", "FAIL")
CURRENT_TIERS = ("PASS", "WARN", "FAIL", "NOT_AVAILABLE")
COLORS = {
    "PASS": "#2f6f5e",
    "WARN": "#b7791f",
    "FAIL": "#b42318",
    "NOT_AVAILABLE": "#64748b",
}
METRICS = {
    "n50": "N50 (bp)",
    "contigs": "Contigs",
    "genome_size": "Genome size (bp)",
    "contamination": "Contamination (%)",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scale_metric(value: float, *, panel_x: float, low: float, span: float) -> float:
    """Map a metric value onto the horizontal axis of an SVG panel."""
    return panel_x + 145 + ((float(value) - low) / span) * 360


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x, y, value, *, size=18, weight=400, fill="#1f2933", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{esc(value)}</text>'
    )


def write_svg(path: Path, width: int, height: int, body: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f6f8fa"/>',
        *body,
        "</svg>",
    ]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def concordance_table(report: pd.DataFrame) -> pd.DataFrame:
    table = pd.crosstab(report["qualibact_tier"], report["qualibact_compat_tier"])
    return table.reindex(index=TIERS, columns=CURRENT_TIERS, fill_value=0)


def write_concordance_figure(path: Path, matrix: pd.DataFrame):
    body = [
        svg_text(60, 65, "Historical and current E. coli QC tiers", size=30, weight=700),
        svg_text(
            60,
            100,
            "Rows: pinned QualiBact metadata; columns: tiers recomputed from current GHRU outputs",
            size=17,
            fill="#52616f",
        ),
    ]
    x0, y0, cell = 250, 175, 135
    for column_index, tier in enumerate(CURRENT_TIERS):
        body.append(
            svg_text(
                x0 + column_index * cell + cell / 2,
                y0 - 28,
                tier,
                weight=700,
                fill=COLORS[tier],
                anchor="middle",
            )
        )
    for row_index, historical_tier in enumerate(TIERS):
        body.append(
            svg_text(
                x0 - 35,
                y0 + row_index * cell + 88,
                historical_tier,
                weight=700,
                fill=COLORS[historical_tier],
                anchor="end",
            )
        )
        for column_index, current_tier in enumerate(CURRENT_TIERS):
            value = int(matrix.loc[historical_tier, current_tier])
            opacity = 0.12 + (value / matrix.to_numpy().max()) * 0.68
            x = x0 + column_index * cell
            y = y0 + row_index * cell
            body.append(
                f'<rect x="{x}" y="{y}" width="{cell - 8}" height="{cell - 8}" '
                f'rx="12" fill="{COLORS[current_tier]}" fill-opacity="{opacity:.3f}"/>'
            )
            body.append(svg_text(x + 64, y + 92, value, size=38, weight=700, anchor="middle"))
    agreement = int(sum(matrix.loc[tier, tier] for tier in TIERS))
    total = int(matrix.to_numpy().sum())
    body.extend(
        [
            svg_text(
                60,
                690,
                f"Exact tier agreement: {agreement}/{total} ({agreement / total:.1%})",
                size=21,
                weight=700,
            ),
            svg_text(
                60,
                730,
                "Discordance is descriptive: historical labels are not treated as ground truth.",
                size=17,
                fill="#52616f",
            ),
        ]
    )
    write_svg(path, 950, 790, body)


def metric_statistics(report: pd.DataFrame) -> pd.DataFrame:
    records = []
    for metric, label in METRICS.items():
        for tier in TIERS:
            values = pd.to_numeric(
                report.loc[report["qualibact_tier"] == tier, metric], errors="coerce"
            ).dropna()
            records.append(
                {
                    "metric": metric,
                    "label": label,
                    "qualibact_tier": tier,
                    "count": len(values),
                    "min": values.min(),
                    "q1": values.quantile(0.25),
                    "median": values.median(),
                    "q3": values.quantile(0.75),
                    "max": values.max(),
                }
            )
    return pd.DataFrame(records)


def write_metric_figure(path: Path, statistics: pd.DataFrame):
    body = [
        svg_text(55, 58, "Observed metrics by historical QualiBact tier", size=30, weight=700),
        svg_text(
            55, 92, "Box plots summarize fresh GHRU-derived measurements", size=17, fill="#52616f"
        ),
    ]
    panel_width, panel_height = 560, 330
    for panel_index, (metric, label) in enumerate(METRICS.items()):
        panel_x = 45 + (panel_index % 2) * 600
        panel_y = 130 + (panel_index // 2) * 390
        rows = statistics[statistics["metric"] == metric].set_index("qualibact_tier")
        low, high = float(rows["min"].min()), float(rows["max"].max())
        span = high - low or 1.0
        body.append(
            f'<rect x="{panel_x}" y="{panel_y}" width="{panel_width}" height="{panel_height}" rx="14" fill="#ffffff" stroke="#d7dee7"/>'
        )
        body.append(svg_text(panel_x + 24, panel_y + 38, label, size=21, weight=700))
        for tier_index, tier in enumerate(TIERS):
            row = rows.loc[tier]
            center_y = panel_y + 100 + tier_index * 72
            scale = partial(scale_metric, panel_x=panel_x, low=low, span=span)
            body.append(
                svg_text(
                    panel_x + 105, center_y + 6, tier, weight=700, fill=COLORS[tier], anchor="end"
                )
            )
            body.append(
                f'<line x1="{scale(row["min"]):.1f}" y1="{center_y}" x2="{scale(row["max"]):.1f}" y2="{center_y}" stroke="#64748b" stroke-width="2"/>'
            )
            body.append(
                f'<rect x="{scale(row["q1"]):.1f}" y="{center_y - 17}" width="{max(2, scale(row["q3"]) - scale(row["q1"])):.1f}" height="34" fill="{COLORS[tier]}" fill-opacity="0.32" stroke="{COLORS[tier]}"/>'
            )
            body.append(
                f'<line x1="{scale(row["median"]):.1f}" y1="{center_y - 20}" x2="{scale(row["median"]):.1f}" y2="{center_y + 20}" stroke="{COLORS[tier]}" stroke-width="4"/>'
            )
        body.append(svg_text(panel_x + 145, panel_y + 307, f"{low:,.2f}", size=13, fill="#64748b"))
        body.append(
            svg_text(
                panel_x + 505, panel_y + 307, f"{high:,.2f}", size=13, fill="#64748b", anchor="end"
            )
        )
    write_svg(path, 1250, 900, body)


def write_report_snapshot(path: Path, report: pd.DataFrame):
    review = report[report["qualibact_compat_tier"].isin(["FAIL", "WARN", "NOT_AVAILABLE"])].copy()
    review = review.sort_values(["qualibact_compat_tier", "sample_id"]).head(10)
    body = [
        svg_text(50, 58, "speccheck 100-sample review snapshot", size=30, weight=700),
        svg_text(
            50,
            92,
            "Samples requiring review under the current pinned compatibility policy",
            size=17,
            fill="#52616f",
        ),
    ]
    headers = ("Sample", "Historical", "Current", "N50", "Contigs", "Reason")
    positions = (55, 260, 400, 535, 660, 790)
    for x, header in zip(positions, headers, strict=True):
        body.append(svg_text(x, 145, header, size=16, weight=700))
    y = 185
    for row in review.to_dict(orient="records"):
        values = (
            row["sample_id"],
            row["qualibact_tier"],
            row["qualibact_compat_tier"],
            f"{int(row['n50']):,}",
            int(row["contigs"]),
            row["reason_summary"],
        )
        for x, value in zip(positions, values, strict=True):
            display = str(value)
            if len(display) > 58:
                display = display[:55] + "..."
            fill = COLORS.get(display, "#1f2933")
            body.append(
                svg_text(
                    x, y, display, size=14, weight=700 if display in COLORS else 400, fill=fill
                )
            )
        body.append(f'<line x1="50" y1="{y + 14}" x2="1195" y2="{y + 14}" stroke="#e2e8f0"/>')
        y += 49
    write_svg(path, 1250, 730, body)


def convert_to_png(svg_paths: list[Path]):
    converter = shutil.which("convert")
    if converter is None:
        return
    for svg_path in svg_paths:
        subprocess.run([converter, str(svg_path), str(svg_path.with_suffix(".png"))], check=True)


def mirror_figures_to_docs(svg_paths: list[Path]):
    DOC_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    for svg_path in svg_paths:
        for source in (svg_path, svg_path.with_suffix(".png")):
            if source.exists():
                shutil.copy2(source, DOC_FIGURE_DIR / f"real_run_100_{source.name}")


def build_assets(run_root: Path, report_root: Path, output: Path):
    report = pd.read_csv(report_root / "report.csv")
    if len(report) != 100 or report["sample_id"].nunique() != 100:
        raise ValueError("The publication cohort must contain exactly 100 unique samples")

    metadata = pd.read_csv(run_root / "metadata.csv")
    resolutions = pd.read_csv(run_root / "ena_resolutions.csv")[["sample_id", "run_accession"]]
    cohort = metadata.merge(resolutions, on="sample_id", validate="one_to_one")
    cohort.to_csv(output / "cohort_accessions.csv", index=False)

    report_output = output / "report"
    report_output.mkdir(parents=True, exist_ok=True)
    for filename in ("report.csv", "report.full.csv", "report.html", "report.xlsx"):
        shutil.copy2(report_root / filename, report_output / filename)

    analysis_dir = output / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    matrix = concordance_table(report)
    matrix.to_csv(analysis_dir / "tier_concordance.csv")
    discordant = report[report["qualibact_tier"] != report["qualibact_compat_tier"]]
    discordant.to_csv(analysis_dir / "discordant_samples.csv", index=False)
    statistics = metric_statistics(report)
    statistics.to_csv(analysis_dir / "metric_distributions.csv", index=False)

    reasons = Counter()
    for value in report.loc[report["reason_summary"] != "none", "reason_summary"]:
        reasons.update(part.strip() for part in str(value).split(";") if part.strip())
    pd.DataFrame(reasons.most_common(), columns=["reason", "sample_count"]).to_csv(
        analysis_dir / "current_reason_counts.csv", index=False
    )

    agreement = int(sum(matrix.loc[tier, tier] for tier in TIERS))
    summary = {
        "sample_count": 100,
        "historical_tiers": report["qualibact_tier"].value_counts().to_dict(),
        "current_compatibility_tiers": report["qualibact_compat_tier"].value_counts().to_dict(),
        "exact_tier_agreement_count": agreement,
        "exact_tier_agreement_fraction": agreement / 100,
        "discordant_count": int(len(discordant)),
        "unidentified_species_count": int((report["species"] == "Unidentified").sum()),
        "criteria_sha256": sha256(ROOT / "speccheck/config/criteria.csv"),
        "qualibact_snapshot_sha256": sha256(ROOT / "speccheck/config/qualibact_snapshot.csv"),
        "pixi_lock_sha256": sha256(ROOT / "pixi.lock"),
        "ghru_assembly_commit": "271e0d9e5593a4e4a59409f12f83e816794ad6a3",
        "ghru_local_patch": {
            "path": "scripts/ghru_disable_upstream_speccheck.patch",
            "sha256": sha256(ROOT / "scripts/ghru_disable_upstream_speccheck.patch"),
            "purpose": "Disable GHRU's bundled speccheck stage so this repository consumes canonical upstream outputs.",
        },
        "selection_rule": "First 70 PASS, 20 WARN, and 10 FAIL rows in the pinned E. coli v1 lists that resolved to paired E. coli ENA reads.",
        "upstream_containers": [
            "shovill_1.1.0-2022Dec.sif",
            "quast_5.2.0--py312pl5321hc60241a_4.sif",
            "checkm2_0.1.0.sif",
            "speciator_4.0.0.sif",
            "sylph_0.1.0.sif",
            "ariba_contam_0.1.1.sif",
        ],
        "downstream_benchmark": {
            "collect_wall_seconds": 26.11,
            "collect_max_rss_kib": 89084,
            "summary_wall_seconds": 31.18,
            "summary_max_rss_kib": 129960,
            "filesystem_note": "Measured on BMRC shared storage; wall time includes metadata latency and HTML/XLSX serialization.",
        },
    }
    (analysis_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    figure_dir = output / "figures"
    svgs = [
        figure_dir / "tier_concordance.svg",
        figure_dir / "metric_distributions.svg",
        figure_dir / "report_snapshot.svg",
    ]
    write_concordance_figure(svgs[0], matrix)
    write_metric_figure(svgs[1], statistics)
    write_report_snapshot(svgs[2], report)
    convert_to_png(svgs)
    mirror_figures_to_docs(svgs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=DEFAULT_RUN_ROOT)
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    build_assets(args.run_root, args.report_root, args.output)


if __name__ == "__main__":
    main()
