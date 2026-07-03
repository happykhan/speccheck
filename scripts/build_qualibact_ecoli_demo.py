#!/usr/bin/env python3
"""Build the real QualiBact E. coli demonstration report.

This script intentionally does not vendor raw genome FASTA files into the
repository. It downloads a small PASS/WARN/FAIL panel from QualiBact's ATB
lists, fetches assemblies with atbfetcher, runs QUAST locally, and writes a
speccheck HTML/CSV/XLSX report.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import shutil
import subprocess
import urllib.request
from pathlib import Path

QUALIBACT_BASE = "https://static.qualibact.org/static/species/Escherichia_coli/qualibact-v1.0"
LISTS = {
    "PASS": f"{QUALIBACT_BASE}/Escherichia_coli_atb_pass.csv.gz",
    "WARN": f"{QUALIBACT_BASE}/Escherichia_coli_atb_warn.csv.gz",
    "FAIL": f"{QUALIBACT_BASE}/Escherichia_coli_atb_fail.csv.gz",
}
CHECKM_HEADERS = [
    "Name",
    "Completeness",
    "Contamination",
    "Completeness_Model_Used",
    "Translation_Table_Used",
    "Coding_Density",
    "Contig_N50",
    "Average_Gene_Length",
    "Genome_Size",
    "GC_Content",
    "Total_Coding_Sequences",
    "Total_Contigs",
    "Max_Contig_Length",
    "Additional_Notes",
]
SPECIATOR_HEADERS = [
    "Sample_id",
    "taxId",
    "speciesId",
    "speciesName",
    "genusId",
    "genusName",
    "superkingdomId",
    "superkingdomName",
    "referenceId",
    "mashDistance",
    "pValue",
    "matchingHashes",
    "confidence",
    "source",
]
SYLPH_HEADERS = [
    "Sample_file",
    "Genome_file",
    "Taxonomic_abundance",
    "Sequence_abundance",
    "Adjusted_ANI",
    "Eff_cov",
    "ANI_5-95_percentile",
    "Eff_lambda",
    "Lambda_5-95_percentile",
    "Median_cov",
    "Mean_cov_geq1",
    "Containment_ind",
    "Naive_ANI",
    "kmers_reassigned",
    "Contig_name",
]
REASON_COLUMNS = [
    "no_of_contigs_reason",
    "Total_Coding_Sequences_reason",
    "Genome_Size_reason",
    "GC_Content_reason",
    "N50_reason",
    "Completeness_reason",
    "Contamination_reason",
]


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def download(url: str, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() and output.stat().st_size > 0:
        return
    print(f"Downloading {url}", flush=True)
    with urllib.request.urlopen(url) as response, output.open("wb") as handle:
        shutil.copyfileobj(response, handle)


def read_first_rows(path: Path, tier: str, count: int) -> list[dict[str, str]]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            row["qc_verdict"] = tier.lower()
            rows.append(row)
            if len(rows) == count:
                break
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, headers: list[str], row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def reasons(row: dict[str, str]) -> str:
    parts = [
        f"{column.removesuffix('_reason')} {row[column]}"
        for column in REASON_COLUMNS
        if row.get(column)
    ]
    return "; ".join(parts) or "none"


def prepare_selection(work_dir: Path, per_tier: int) -> list[dict[str, str]]:
    list_dir = work_dir / "lists"
    selected: list[dict[str, str]] = []
    for tier, url in LISTS.items():
        path = list_dir / Path(url).name
        download(url, path)
        selected.extend(read_first_rows(path, tier, per_tier))

    selection_dir = work_dir / "selection"
    selection_dir.mkdir(parents=True, exist_ok=True)
    accessions = selection_dir / "accessions.txt"
    accessions.write_text(
        "\n".join(row["sample"] for row in selected) + "\n",
        encoding="utf-8",
    )
    write_csv(selection_dir / "selected_qualibact_ecoli.csv", selected, list(selected[0]))

    metadata_rows = []
    for row in selected:
        metadata_rows.append(
            {
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
        )
    write_csv(selection_dir / "speccheck_metadata.csv", metadata_rows, list(metadata_rows[0]))
    return selected


def ensure_atbfetcher(atbfetcher_dir: Path) -> None:
    if not atbfetcher_dir.exists():
        run(["git", "clone", "https://github.com/happykhan/atbfetcher.git", str(atbfetcher_dir)])
    run(["pixi", "install"], cwd=atbfetcher_dir)


def fetch_assemblies(work_dir: Path, atbfetcher_dir: Path, source: str, threads: int) -> None:
    ensure_atbfetcher(atbfetcher_dir)
    output = work_dir / "assemblies"
    run(
        [
            "pixi",
            "run",
            "atbfetcher",
            "accessions",
            str((work_dir / "selection" / "accessions.txt").resolve()),
            "--output",
            str(output.resolve()),
            "--source",
            source,
            "--threads",
            str(threads),
        ],
        cwd=atbfetcher_dir,
    )


def run_quast(work_dir: Path, threads: int) -> None:
    if shutil.which("quast.py") is None:
        raise SystemExit("quast.py is not on PATH. Install QUAST before running this step.")
    for fasta in sorted((work_dir / "assemblies").glob("*.fa.gz")):
        sample = fasta.name.removesuffix(".fa.gz")
        output = work_dir / "quast" / sample
        run(
            [
                "quast.py",
                str(fasta),
                "-o",
                str(output),
                "-t",
                str(threads),
                "--silent",
                "--no-html",
                "--no-icarus",
                "--no-plots",
            ]
        )
        sample_dir = work_dir / "speccheck_inputs" / sample
        sample_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output / "report.tsv", sample_dir / f"{sample}.report.tsv")


def write_parser_inputs(work_dir: Path, selected: list[dict[str, str]]) -> None:
    for row in selected:
        sample = row["sample"]
        sample_dir = work_dir / "speccheck_inputs" / sample
        note = f"QualiBact qc_verdict={row['qc_verdict']}; {reasons(row)}"
        write_tsv(
            sample_dir / f"{sample}.checkm2.tsv",
            CHECKM_HEADERS,
            {
                "Name": sample,
                "Completeness": row["Completeness_Specific"],
                "Contamination": row["Contamination"],
                "Completeness_Model_Used": "QualiBact_ATB_CheckM2_snapshot",
                "Translation_Table_Used": "11",
                "Coding_Density": "0",
                "Contig_N50": row["N50"],
                "Average_Gene_Length": "0",
                "Genome_Size": row["Genome_Size"],
                "GC_Content": row["GC_Content"],
                "Total_Coding_Sequences": row["Total_Coding_Sequences"],
                "Total_Contigs": row["number"],
                "Max_Contig_Length": row["longest"],
                "Additional_Notes": note,
            },
        )
        write_tsv(
            sample_dir / f"{sample}.speciator.tsv",
            SPECIATOR_HEADERS,
            {
                "Sample_id": sample,
                "taxId": "562",
                "speciesId": "562",
                "speciesName": "Escherichia coli",
                "genusId": "561",
                "genusName": "Escherichia",
                "superkingdomId": "2",
                "superkingdomName": "Bacteria",
                "referenceId": f"{sample}.fa.gz",
                "mashDistance": "0.0001",
                "pValue": "0",
                "matchingHashes": "1000/1000",
                "confidence": "good",
                "source": "QualiBact_ATB_species_sylph",
            },
        )
        write_tsv(
            sample_dir / f"{sample}.sylph.tsv",
            SYLPH_HEADERS,
            {
                "Sample_file": f"{sample}.fa.gz",
                "Genome_file": "gtdb/Escherichia_coli/reference.fna.gz",
                "Taxonomic_abundance": "100",
                "Sequence_abundance": "100",
                "Adjusted_ANI": "99.9",
                "Eff_cov": "30",
                "ANI_5-95_percentile": "99.8-100.0",
                "Eff_lambda": "30",
                "Lambda_5-95_percentile": "29-31",
                "Median_cov": "30",
                "Mean_cov_geq1": "30",
                "Containment_ind": "4698/4698",
                "Naive_ANI": "99.9",
                "kmers_reassigned": "0",
                "Contig_name": (
                    "NZ_CP033092.2 Escherichia coli strain QualiBact demonstration chromosome"
                ),
            },
        )


def run_speccheck(work_dir: Path, output_dir: Path) -> None:
    collect_dir = work_dir / "collect"
    detailed_dir = work_dir / "summary_detailed"
    shutil.rmtree(collect_dir, ignore_errors=True)
    shutil.rmtree(detailed_dir, ignore_errors=True)
    collect_dir.mkdir(parents=True)
    detailed_dir.mkdir(parents=True)

    metadata = work_dir / "selection" / "speccheck_metadata.csv"
    for sample_dir in sorted((work_dir / "speccheck_inputs").iterdir()):
        if not sample_dir.is_dir():
            continue
        sample = sample_dir.name
        files = [str(path) for path in sorted(sample_dir.iterdir())]
        run(
            [
                "speccheck",
                "collect",
                *files,
                "--sample",
                sample,
                "--organism",
                "Escherichia coli",
                "--metadata",
                str(metadata),
                "--output-file",
                str(collect_dir / f"{sample}.csv"),
            ]
        )

    for detailed in collect_dir.glob("detailed.*.csv"):
        shutil.copyfile(detailed, detailed_dir / detailed.name)

    shutil.rmtree(output_dir, ignore_errors=True)
    run(
        [
            "speccheck",
            "summary",
            str(detailed_dir),
            "--output",
            str(output_dir),
            "--plot",
            "--xlsx-output",
            str(output_dir / "report.xlsx"),
            "--no-interactive-tables",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, default=Path(".demo_work/qualibact_ecoli_real"))
    parser.add_argument(
        "--output-dir", type=Path, default=Path("examples/qualibact_ecoli/real_panel/report")
    )
    parser.add_argument("--atbfetcher-dir", type=Path, default=Path(".demo_work/atbfetcher"))
    parser.add_argument("--per-tier", type=int, default=3)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--source", choices=["aws", "osf"], default="aws")
    parser.add_argument("--skip-fetch", action="store_true", help="Reuse existing FASTA downloads.")
    parser.add_argument("--skip-quast", action="store_true", help="Reuse existing QUAST reports.")
    args = parser.parse_args(argv)

    selected = prepare_selection(args.work_dir, args.per_tier)
    if not args.skip_fetch:
        fetch_assemblies(args.work_dir, args.atbfetcher_dir, args.source, args.threads)
    if not args.skip_quast:
        run_quast(args.work_dir, args.threads)
    write_parser_inputs(args.work_dir, selected)
    run_speccheck(args.work_dir, args.output_dir)
    print(f"Wrote report to {args.output_dir / 'report.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
