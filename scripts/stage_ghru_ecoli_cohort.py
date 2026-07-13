#!/usr/bin/env python3
"""Stage a read-backed E. coli cohort for GHRU-assembly."""

from __future__ import annotations

import argparse
import csv
import gzip
import shutil
from collections import OrderedDict
from pathlib import Path

import requests

QUALIBACT_BASE = "https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0"
LISTS = OrderedDict(
    [
        ("PASS", f"{QUALIBACT_BASE}/Escherichia_coli_atb_pass.csv.gz"),
        ("WARN", f"{QUALIBACT_BASE}/Escherichia_coli_atb_warn.csv.gz"),
        ("FAIL", f"{QUALIBACT_BASE}/Escherichia_coli_atb_fail.csv.gz"),
    ]
)
UA = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
TRIPLET_IDS = ["SAMN42766885", "SAMN42764706", "SAMN42765982"]
REASON_COLUMNS = [
    "no_of_contigs_reason",
    "Total_Coding_Sequences_reason",
    "Genome_Size_reason",
    "GC_Content_reason",
    "N50_reason",
    "Completeness_reason",
    "Contamination_reason",
]
METADATA_COLUMNS = [
    "sample_id",
    "qualibact_tier",
    "qualibact_species_sylph",
    "qualibact_reasons",
    "qualibact_N50",
    "qualibact_contigs",
    "qualibact_genome_size",
    "qualibact_gc_content",
    "qualibact_completeness_specific",
    "qualibact_contamination",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--selection-csv", type=Path)
    parser.add_argument("--samples", nargs="*", default=None)
    parser.add_argument("--preset", choices=["triplet"], default=None)
    parser.add_argument("--pass-count", type=int, default=0)
    parser.add_argument("--warn-count", type=int, default=0)
    parser.add_argument("--fail-count", type=int, default=0)
    parser.add_argument("--download-reads", action="store_true", default=False)
    parser.add_argument("--no-download-reads", dest="download_reads", action="store_false")
    parser.add_argument("--include-non-ecoli", action="store_true")
    return parser.parse_args()


def request_stream(url: str):
    response = requests.get(url, headers=UA, timeout=120, stream=True)
    response.raise_for_status()
    return response


def download_file(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size > 0:
        return
    with request_stream(url) as response, output.open("wb") as handle:
        shutil.copyfileobj(response.raw, handle)


def reasons(row: dict[str, str]) -> str:
    parts = [f"{col.removesuffix('_reason')} {row[col]}" for col in REASON_COLUMNS if row.get(col)]
    return "; ".join(parts) or "none"


def metadata_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "sample_id": row["sample"],
        "qualibact_tier": row["qc_verdict"].upper(),
        "qualibact_species_sylph": row["species_sylph"],
        "qualibact_reasons": reasons(row),
        "qualibact_N50": row["N50"],
        "qualibact_contigs": row["number"],
        "qualibact_genome_size": row["Genome_Size"],
        "qualibact_gc_content": row["GC_Content"],
        "qualibact_completeness_specific": row["Completeness_Specific"],
        "qualibact_contamination": row["Contamination"],
    }


def load_selection_rows(selection_csv: Path) -> list[dict[str, str]]:
    with selection_csv.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def download_list_csv(url: str, output: Path) -> list[dict[str, str]]:
    download_file(url, output)
    with gzip.open(output, "rt", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def resolve_ena(sample_id: str) -> dict[str, str] | None:
    url = (
        "https://www.ebi.ac.uk/ena/portal/api/filereport"
        f"?accession={sample_id}&result=read_run&fields=run_accession,fastq_ftp,library_layout,"
        "sample_accession,scientific_name&format=tsv"
    )
    response = requests.get(url, headers=UA, timeout=60)
    response.raise_for_status()
    lines = [line for line in response.text.strip().splitlines() if line.strip()]
    if len(lines) < 2:
        return None
    fields = lines[1].split("\t")
    if len(fields) < 5:
        return None
    run_accession, fastq_ftp, library_layout, _sample_accession, scientific_name = fields[:5]
    if scientific_name != "Escherichia coli":
        return None
    if library_layout != "PAIRED":
        return None
    fastqs = fastq_ftp.split(";")
    if len(fastqs) != 2:
        return None
    return {
        "run_accession": run_accession,
        "fastq1": fastqs[0],
        "fastq2": fastqs[1],
    }


def select_triplet(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    sample_map = {row["sample"]: row for row in rows}
    missing = [sample for sample in TRIPLET_IDS if sample not in sample_map]
    if missing:
        raise SystemExit(f"Triplet sample(s) missing from selection CSV: {', '.join(missing)}")
    return [sample_map[sample] for sample in TRIPLET_IDS]


def select_explicit(rows: list[dict[str, str]], samples: list[str]) -> list[dict[str, str]]:
    sample_map = {row["sample"]: row for row in rows}
    missing = [sample for sample in samples if sample not in sample_map]
    if missing:
        raise SystemExit(f"Requested sample(s) not found in selection CSV: {', '.join(missing)}")
    return [sample_map[sample] for sample in samples]


def select_counts(
    run_root: Path, pass_count: int, warn_count: int, fail_count: int
) -> list[dict[str, str]]:
    quotas = OrderedDict([("PASS", pass_count), ("WARN", warn_count), ("FAIL", fail_count)])
    selected: list[dict[str, str]] = []
    ena_cache: dict[str, dict[str, str] | None] = {}
    list_dir = run_root / "lists"

    for tier, count in quotas.items():
        if count <= 0:
            continue
        rows = download_list_csv(LISTS[tier], list_dir / Path(LISTS[tier]).name)
        chosen = 0
        for row in rows:
            if row.get("species_sylph") != "Escherichia coli":
                continue
            sample = row["sample"]
            if sample in ena_cache:
                ena = ena_cache[sample]
            else:
                ena = resolve_ena(sample)
                ena_cache[sample] = ena
            if not ena:
                continue
            selected.append(row)
            chosen += 1
            if chosen == count:
                break
        if chosen != count:
            raise SystemExit(
                f"Could not resolve {count} read-backed {tier} E. coli samples from QualiBact"
            )
    return selected


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def choose_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.selection_csv:
        rows = load_selection_rows(args.selection_csv)
        if args.preset == "triplet":
            return select_triplet(rows)
        if args.samples:
            return select_explicit(rows, args.samples)
        return rows
    if args.preset == "triplet":
        rows = load_selection_rows(
            Path("examples/qualibact_ecoli/real_panel/input/selected_qualibact_ecoli.csv")
        )
        return select_triplet(rows)
    if args.samples:
        rows = load_selection_rows(
            Path("examples/qualibact_ecoli/real_panel/input/selected_qualibact_ecoli.csv")
        )
        return select_explicit(rows, args.samples)
    return select_counts(args.run_root, args.pass_count, args.warn_count, args.fail_count)


def stage_reads(selected: list[dict[str, str]], run_root: Path, download_reads: bool) -> None:
    read_dir = run_root / "reads"
    read_dir.mkdir(parents=True, exist_ok=True)
    samplesheet = run_root / "samplesheet.csv"
    metadata_csv = run_root / "metadata.csv"
    ena_cache_file = run_root / "ena_resolutions.csv"
    selection_dir = run_root / "selection"
    selection_dir.mkdir(parents=True, exist_ok=True)

    write_csv(selection_dir / "selected_qualibact_ecoli.csv", selected, list(selected[0].keys()))
    write_csv(
        selection_dir / "speccheck_metadata.csv",
        [metadata_row(row) for row in selected],
        METADATA_COLUMNS,
    )

    ena_rows: list[dict[str, str]] = []
    with (
        samplesheet.open("w", encoding="utf-8", newline="") as sheet_handle,
        metadata_csv.open("w", encoding="utf-8", newline="") as meta_handle,
    ):
        sheet_writer = csv.writer(sheet_handle)
        meta_writer = csv.DictWriter(meta_handle, fieldnames=METADATA_COLUMNS)
        sheet_writer.writerow(
            ["sample_id", "short_reads1", "short_reads2", "long_reads", "genome_size"]
        )
        meta_writer.writeheader()

        for row in selected:
            sample = row["sample"]
            ena = resolve_ena(sample)
            if not ena:
                raise SystemExit(f"No paired E. coli ENA read set resolved for {sample}")

            fastq1_url = f"https://{ena['fastq1']}"
            fastq2_url = f"https://{ena['fastq2']}"
            fastq1_path = read_dir / Path(ena["fastq1"]).name
            fastq2_path = read_dir / Path(ena["fastq2"]).name

            if download_reads:
                download_file(fastq1_url, fastq1_path)
                download_file(fastq2_url, fastq2_path)

            ena_rows.append(
                {
                    "sample_id": sample,
                    "run_accession": ena["run_accession"],
                    "fastq1_url": fastq1_url,
                    "fastq2_url": fastq2_url,
                }
            )
            sheet_writer.writerow([sample, str(fastq1_path), str(fastq2_path), "", ""])
            meta_writer.writerow(metadata_row(row))

    write_csv(ena_cache_file, ena_rows, ["sample_id", "run_accession", "fastq1_url", "fastq2_url"])


def main() -> int:
    args = parse_args()
    if (
        not args.selection_csv
        and not args.preset
        and not args.samples
        and not any([args.pass_count, args.warn_count, args.fail_count])
    ):
        raise SystemExit("Provide --selection-csv, --preset, --samples, or pass/warn/fail counts")

    args.run_root.mkdir(parents=True, exist_ok=True)
    selected = choose_rows(args)

    if not args.include_non_ecoli:
        selected = [row for row in selected if row.get("species_sylph") == "Escherichia coli"]

    if not selected:
        raise SystemExit("No samples selected for staging")

    stage_reads(selected, args.run_root, args.download_reads)
    print(f"Staged {len(selected)} read-backed E. coli samples in {args.run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
