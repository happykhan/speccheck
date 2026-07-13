#!/usr/bin/env python3
"""Create manuscript-ready static assets from committed example reports."""

from __future__ import annotations

import csv
import html
import shutil
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "examples/qualibact_ecoli/real_panel/report"
REPORT_CSV = REPORT_DIR / "report.full.csv"
ASSET_DIR = ROOT / "examples/qualibact_ecoli/manuscript_assets"
DOC_FIGURE_DIR = ROOT / "docs/assets/figures"


def read_rows() -> list[dict[str, str]]:
    if not REPORT_CSV.exists():
        raise FileNotFoundError(f"Expected merged report at {REPORT_CSV}")
    with REPORT_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x: int, y: int, text: str, size: int = 22, weight: int = 400, fill: str = "#1f2933"):
    return (
        f'<text x="{x}" y="{y}" font-family="Arial, Helvetica, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{esc(text)}</text>'
    )


def rounded_rect(x: int, y: int, w: int, h: int, fill: str, stroke: str = "#cbd5df"):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" />'
    )


def write_svg(path: Path, width: int, height: int, body: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f6f8fa" />',
        *body,
        "</svg>",
    ]
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def workflow_svg(path: Path):
    body = [
        svg_text(60, 70, "speccheck workflow", size=34, weight=700),
        svg_text(
            60,
            108,
            "Species-aware genome QC collection, validation, and reporting",
            size=18,
            fill="#52616f",
        ),
    ]
    boxes = [
        (
            60,
            160,
            230,
            155,
            "Upstream QC",
            ["QUAST", "CheckM2", "Sylph", "Speciator", "ARIBA", "depth"],
        ),
        (350, 160, 230, 155, "collect", ["Parse tool outputs", "Apply criteria"]),
        (640, 160, 230, 155, "criteria", ["Species-specific", "pass/fail thresholds"]),
        (930, 160, 230, 155, "summary", ["Merge samples", "Generate reports"]),
        (1220, 160, 230, 155, "Outputs", ["CSV", "HTML", "XLSX", "figures"]),
    ]
    for x, y, w, h, title, subtitle in boxes:
        body.append(rounded_rect(x, y, w, h, "#ffffff"))
        body.append(svg_text(x + 24, y + 42, title, size=24, weight=700))
        line = 0
        for part in subtitle:
            body.append(svg_text(x + 24, y + 72 + line * 21, part, size=15, fill="#52616f"))
            line += 1
        if x < 1220:
            body.append(
                f'<path d="M{x + w + 18},{y + 78} L{x + w + 56},{y + 78}" stroke="#1f5f8b" stroke-width="5" marker-end="url(#arrow)" />'
            )
    body.insert(
        0,
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#1f5f8b"/></marker></defs>',
    )
    body.extend(
        [
            rounded_rect(190, 385, 1120, 120, "#edf5fb", "#b8d3e5"),
            svg_text(230, 435, "Manuscript example", size=26, weight=700),
            svg_text(
                230,
                473,
                "A real QualiBact E. coli PASS/WARN/FAIL panel is converted into speccheck reports for reproducible demonstration.",
                size=18,
                fill="#52616f",
            ),
        ]
    )
    write_svg(path, 1520, 565, body)


def outcomes_svg(path: Path, rows: list[dict[str, str]]):
    tier_counts = Counter(row["qualibact_tier"] for row in rows)
    compat_counts = Counter(row["qualibact_compat_tier"] for row in rows)
    sample_count = len(rows)
    body = [
        svg_text(60, 70, "Real E. coli demonstration panel", size=34, weight=700),
        svg_text(
            60,
            108,
            "QualiBact tier labels and computed compatibility-tier outcomes",
            size=18,
            fill="#52616f",
        ),
    ]
    colors = {
        "PASS": "#2f6f5e",
        "WARN": "#b7791f",
        "FAIL": "#b42318",
        "PASSED": "#2f6f5e",
        "FAILED": "#b42318",
    }
    x = 70
    for label in ["PASS", "WARN", "FAIL"]:
        count = tier_counts[label]
        body.append(rounded_rect(x, 165, 250, 160, "#ffffff"))
        body.append(svg_text(x + 28, 215, label, size=28, weight=700, fill=colors[label]))
        body.append(svg_text(x + 28, 285, str(count), size=56, weight=700, fill=colors[label]))
        body.append(svg_text(x + 95, 285, "genomes", size=20, fill="#52616f"))
        x += 290
    x = 955
    for label in ["PASS", "WARN", "FAIL"]:
        count = compat_counts[label]
        body.append(rounded_rect(x, 165, 250, 160, "#ffffff"))
        body.append(
            svg_text(x + 28, 215, f"compat {label}", size=23, weight=700, fill=colors[label])
        )
        body.append(svg_text(x + 28, 285, str(count), size=56, weight=700, fill=colors[label]))
        body.append(svg_text(x + 95, 285, "genomes", size=20, fill="#52616f"))
        x += 290
    body.append(rounded_rect(70, 380, 1365, 165, "#ffffff"))
    body.append(svg_text(105, 425, "Interpretation", size=24, weight=700))
    body.append(
        svg_text(
            105,
            465,
            f"This panel currently contains {sample_count} real GHRU-derived assemblies with metadata-pinned QualiBact PASS/WARN/FAIL labels.",
            size=18,
            fill="#52616f",
        )
    )
    body.append(
        svg_text(
            105,
            505,
            "Compatibility tiers are computed from current observed metrics, so they can diverge from older QualiBact metadata labels when upstream assemblies differ.",
            size=18,
            fill="#52616f",
        )
    )
    write_svg(path, 1520, 620, body)


def report_snapshot_svg(path: Path, rows: list[dict[str, str]]):
    sample_count = len(rows)
    tier_counts = Counter(row["qualibact_tier"] for row in rows)
    compat_counts = Counter(row["qualibact_compat_tier"] for row in rows)
    compat_summary = ", ".join(
        f"{compat_counts[label]} {label}" for label in ["PASS", "WARN", "FAIL"] if compat_counts[label]
    ) or "0 PASS"
    tier_summary = ", ".join(
        f"{tier_counts[label]} {label}" for label in ["PASS", "WARN", "FAIL"] if tier_counts[label]
    ) or "0 PASS"
    body = [
        svg_text(60, 70, "speccheck report snapshot", size=34, weight=700),
        svg_text(
            60,
            108,
            "Static paper-friendly rendering of the real-panel report summary",
            size=18,
            fill="#52616f",
        ),
        rounded_rect(60, 145, 1400, 170, "#ffffff"),
        svg_text(95, 200, f"{sample_count} samples", size=28, weight=700),
        svg_text(95, 240, tier_summary, size=20, fill="#52616f"),
        svg_text(520, 200, "Compatibility tiers", size=28, weight=700, fill="#1f5f8b"),
        svg_text(520, 240, compat_summary, size=20, fill="#52616f"),
        svg_text(980, 200, "Outputs", size=28, weight=700),
        svg_text(980, 240, "report.csv, report.html, report.xlsx", size=20, fill="#52616f"),
        rounded_rect(60, 360, 1400, 520, "#ffffff"),
        svg_text(95, 410, "Real-panel sample table", size=24, weight=700),
    ]
    headers = ["Sample", "QualiBact", "Compat", "N50", "Contigs", "Reason"]
    xs = [95, 300, 475, 660, 790, 930]
    for x, header in zip(xs, headers, strict=False):
        body.append(svg_text(x, 455, header, size=17, weight=700, fill="#334155"))
    y = 490
    for row in rows:
        compat_fill = {"PASS": "#2f6f5e", "WARN": "#b7791f", "FAIL": "#b42318"}[
            row["qualibact_compat_tier"]
        ]
        tier_fill = {"PASS": "#2f6f5e", "WARN": "#b7791f", "FAIL": "#b42318"}[row["qualibact_tier"]]
        reason = row["qualibact_compat_reasons"]
        if len(reason) > 56:
            reason = reason[:53] + "..."
        values = [
            row["sample_id"],
            row["qualibact_tier"],
            row["qualibact_compat_tier"],
            f"{int(float(row['Quast.N50'])):,}",
            row["Quast.# contigs (>= 0 bp)"],
            reason,
        ]
        for x, value in zip(xs, values, strict=False):
            fill = "#1f2933"
            weight = 400
            if value == row["qualibact_tier"]:
                fill = tier_fill
                weight = 700
            if value == row["qualibact_compat_tier"]:
                fill = compat_fill
                weight = 700
            body.append(svg_text(x, y, value, size=15, weight=weight, fill=fill))
        body.append(f'<line x1="95" y1="{y + 13}" x2="1415" y2="{y + 13}" stroke="#e5eaf0" />')
        y += 43
    write_svg(path, 1520, 940, body)


def write_summary_table(rows: list[dict[str, str]]):
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    columns = [
        "sample_id",
        "qualibact_tier",
        "qualibact_compat_tier",
        "qualibact_compat_reasons",
        "all_checks_passed",
        "Quast.N50",
        "Quast.# contigs (>= 0 bp)",
        "Checkm.Completeness",
        "Checkm.Contamination",
        "qualibact_reasons",
    ]
    csv_path = ASSET_DIR / "real_panel_summary_table.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in columns})

    md_path = ASSET_DIR / "real_panel_summary_table.md"
    lines = [
        "| Sample | QualiBact tier | Compatibility tier | speccheck binary | N50 | Contigs | CheckM completeness | CheckM contamination | Compatibility reasons |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {sample_id} | {qualibact_tier} | {compat_tier} | {all_checks_passed} | {n50:,} | {contigs} | {comp:.1f} | {contam:.2f} | {reasons} |".format(
                sample_id=row["sample_id"],
                qualibact_tier=row["qualibact_tier"],
                compat_tier=row["qualibact_compat_tier"],
                all_checks_passed=row["all_checks_passed"],
                n50=int(float(row["Quast.N50"])),
                contigs=row["Quast.# contigs (>= 0 bp)"],
                comp=float(row["Checkm.Completeness"]),
                contam=float(row["Checkm.Contamination"]),
                reasons=row["qualibact_compat_reasons"].replace("|", "\\|"),
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def convert_svgs_to_png(paths: list[Path]):
    converter = shutil.which("convert")
    if converter is None:
        return
    for svg_path in paths:
        png_path = svg_path.with_suffix(".png")
        subprocess.run([converter, str(svg_path), str(png_path)], check=True)


def mirror_to_docs(paths: list[Path]):
    DOC_FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    mirrored = []
    for path in paths:
        target = DOC_FIGURE_DIR / path.name
        target.write_bytes(path.read_bytes())
        mirrored.append(target)
        png = path.with_suffix(".png")
        if png.exists():
            png_target = DOC_FIGURE_DIR / png.name
            png_target.write_bytes(png.read_bytes())
            mirrored.append(png_target)
    return mirrored


def main():
    rows = read_rows()
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    svg_paths = [
        ASSET_DIR / "speccheck_workflow.svg",
        ASSET_DIR / "real_panel_outcomes.svg",
        ASSET_DIR / "real_panel_report_snapshot.svg",
    ]
    workflow_svg(svg_paths[0])
    outcomes_svg(svg_paths[1], rows)
    report_snapshot_svg(svg_paths[2], rows)
    write_summary_table(rows)
    convert_svgs_to_png(svg_paths)
    mirror_to_docs(svg_paths)
    print(f"Wrote manuscript assets to {ASSET_DIR}")
    print(f"Mirrored figures to {DOC_FIGURE_DIR}")


if __name__ == "__main__":
    main()
