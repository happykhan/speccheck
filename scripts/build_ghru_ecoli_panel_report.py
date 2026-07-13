#!/usr/bin/env python3
"""Build the committed real-panel example report from a GHRU output tree."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from speccheck.config import get_default_criteria_path
from speccheck.main import collect_ghru, summary
from speccheck.report import get_default_template_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ghru_output_dir", type=Path, help="GHRU output directory")
    parser.add_argument(
        "--metadata",
        type=Path,
        required=True,
        help="CSV with sample_id and metadata columns for the panel",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Optional Nextflow work directory to search for unpublished depth files",
    )
    parser.add_argument(
        "--collect-dir",
        type=Path,
        default=Path(".demo_work/ghru_ecoli_panel/triplet/collect"),
        help="Destination for per-sample collected CSVs",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("examples/qualibact_ecoli/real_panel/report"),
        help="Destination for the merged report outputs",
    )
    parser.add_argument(
        "--organism",
        default="Escherichia coli",
        help="Organism override applied during collect-pipeline --layout ghru",
    )
    args = parser.parse_args(argv)

    shutil.rmtree(args.collect_dir, ignore_errors=True)
    shutil.rmtree(args.output_dir, ignore_errors=True)

    collect_ghru(
        str(args.ghru_output_dir),
        str(args.collect_dir),
        get_default_criteria_path(),
        organism=args.organism,
        metadata_file=str(args.metadata),
        work_dir=str(args.work_dir) if args.work_dir else None,
    )
    summary(
        str(args.collect_dir),
        str(args.output_dir),
        "Speciator.speciesName",
        "sample_id",
        get_default_template_path(),
        True,
        xlsx_output=str(args.output_dir / "report.xlsx"),
        interactive_tables=False,
        qualifyr_style=True,
        qualibact_compat=True,
    )
    print(f"Wrote report to {args.output_dir / 'report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
