import logging
import operator as op_from_module
import os
import re
from collections.abc import Iterable


def collect_files(all_files, module_list):
    # Execute checks for each file using discovered modules
    recovered_values = {}
    for filepath in all_files:
        logging.debug("Checking %s", filepath)
        for module in module_list:
            current_module = module(filepath)
            if current_module.has_valid_filename and current_module.has_valid_fileformat:
                logging.debug("File %s passed checks from %s", filepath, module.__name__)
                # Fetch values and criteria
                recovered_values[module.__name__] = current_module.fetch_values()
    if not recovered_values:
        logging.warning("No files passed the checks.")
    return recovered_values


def check_criteria(field, result):
    test_result = True
    software = field["software"]

    # --- Handle DepthParser hybrid output (short + long) ---
    # result["DepthParser"] can be a dict (short or long) or list (hybrid)
    if software.startswith("DepthParser"):
        # Determine which type of read (short or long) to check
        read_type = None
        if software.endswith(".short"):
            read_type = "short"
        elif software.endswith(".long"):
            read_type = "long"

        depth_entries = result.get("DepthParser")

        # If it's hybrid (list), pick the matching read type
        if isinstance(depth_entries, list):
            matched = next(
                (entry for entry in depth_entries if entry.get("Read_type") == read_type), None
            )
            if not matched:
                logging.warning("No matching read type (%s) found for DepthParser", read_type)
                return False
            field_value = matched[field["field"]]
        else:
            # Single short or long file
            field_value = depth_entries[field["field"]]
    else:
        field_value = result[field["field"]]

    if field["operator"] == "regex":
        if not re.match(field["value"], result[field["field"]]):
            logging.warning(
                "Failed check for %s: %s does not match regex %s",
                field["software"],
                field["field"],
                field["value"],
            )
            test_result = False
    else:
        field_value = result[field["field"]]
        operator = field["operator"]
        criteria_value = field["value"]

        if operator == "=":
            operator = "=="
        ops = {
            "==": op_from_module.eq,
            "!=": op_from_module.ne,
            "<": op_from_module.lt,
            "<=": op_from_module.le,
            ">": op_from_module.gt,
            ">=": op_from_module.ge,
        }
        if not ops[operator](field_value, criteria_value):
            logging.warning(
                "Failed check for %s: %s %s %s",
                field["software"],
                field["field"],
                field["operator"],
                field["value"],
            )
            test_result = False
    return test_result


def _extract_accessions_from_genome_paths(raw: str | Iterable[str] | None):
    """Return semicolon-joined accession IDs from Sylph genome path(s).

    Accepts a single string (possibly semicolon-delimited) or an iterable of strings.
    Path examples:
        gtdb_genomes_reps_r220/database/GCF/000/742/135/GCF_000742135.1_genomic.fna.gz
    We extract the final filename, drop suffix `_genomic.fna.gz` (or .fna/.fa[.gz])
    and return just the accession (e.g. `GCF_000742135.1`).
    If parsing fails, we fall back to original token.
    """
    if raw is None:
        return ""

    # Normalize into list of path tokens
    if isinstance(raw, str):
        parts = [p for p in raw.split(";") if p]
    else:
        parts = []
        for item in raw:
            if not item:
                continue
            parts.extend([p for p in str(item).split(";") if p])

    cleaned: list[str] = []
    for p in parts:
        fname = p.rsplit("/", 1)[-1]
        # Remove common genome file suffixes
        for suf in ["_genomic.fna.gz", "_genomic.fna", ".fna.gz", ".fna", ".fa.gz", ".fa"]:
            if fname.endswith(suf):
                fname = fname[: -len(suf)]
                break
        cleaned.append(fname)
    return ";".join(cleaned)


def write_to_file(output_file, qc_report):
    """Write results to CSV.

    Behavior:
    - If the report looks like a full speccheck QC report (has module-prefixed keys), write two files:
        1) A concise CSV at `output_file` with a fixed column schema/order.
        2) A detailed CSV alongside it, prefixed as `detailed.<basename>`, containing all keys
           using the legacy ordering (backward compatible).
    - Otherwise (e.g., unit tests or ad-hoc dicts), preserve legacy behavior and only write
      the simple CSV with natural ordering.
    """
    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Columns required in concise output and their explicit order
    concise_columns = [
        "sample_id",
        "all_checks_passed",
        "Speciator.all_checks_passed",
        "Speciator.speciesName",
        "Depth.all_checks_passed",
        "Depth.Depth",
        "Depth.Read_type",
        "Sylph.all_checks_passed",
        "Sylph.top_species",
        "Sylph.top_taxonomic_abundance",
        "Quast.all_checks_passed",
        "Quast.# contigs (>= 0 bp).check",
        "Quast.# contigs",
        "Quast.N50.check",
        "Quast.N50",
        "Quast.Total length (>= 0 bp).check",
        "Quast.Total length",
        "Quast.GC (%).check",
        "Quast.GC (%)",
        "Quast.Largest contig",
        "Checkm.all_checks_passed",
        "Checkm.Completeness.check",
        "Checkm.Completeness",
        "Checkm.Contamination.check",
        "Checkm.Contamination",
        "Sylph.genomes",
    ]

    # Heuristic: determine if this is a full speccheck QC report
    looks_like_qc = (
        any(k.startswith(("Speciator.", "Depth.", "Sylph.", "Quast.", "Checkm.")) for k in qc_report)
        or ("sample_id" in qc_report and "all_checks_passed" in qc_report)
    )

    if looks_like_qc:
        # Sanitize Sylph.genomes to contain only accession IDs
        if "Sylph.genomes" in qc_report:
            qc_report = dict(qc_report)  # shallow copy to avoid mutating caller
            qc_report["Sylph.genomes"] = _extract_accessions_from_genome_paths(
                qc_report.get("Sylph.genomes")
            )
        # 1) Write detailed CSV (legacy, all fields) as detailed.<basename>
        detailed_dir = os.path.dirname(output_file)
        base = os.path.basename(output_file)
        detailed_path = os.path.join(detailed_dir, f"detailed.{base}") if detailed_dir else f"detailed.{base}"

        sample_id_cols = [k for k in qc_report.keys() if k in ["Sample", "sample_id"]]
        all_checks_passed_cols = sorted([k for k in qc_report.keys() if k.endswith("all_checks_passed")])
        check_cols = sorted([k for k in qc_report.keys() if k.endswith(".check")])
        other_cols = sorted(
            [
                k
                for k in qc_report.keys()
                if k not in sample_id_cols
                and not k.endswith("all_checks_passed")
                and not k.endswith(".check")
            ]
        )
        detailed_keys = sample_id_cols + all_checks_passed_cols + check_cols + other_cols

        with open(detailed_path, "w", encoding="utf-8") as f_det:
            f_det.write(",".join(detailed_keys) + "\n")
            f_det.write(",".join(str(qc_report.get(key, "")) for key in detailed_keys) + "\n")
        logging.info("Detailed results written to %s", detailed_path)

        # 2) Write concise CSV with only the requested columns, in that exact order
        with open(output_file, "w", encoding="utf-8") as f_out:
            f_out.write(",".join(concise_columns) + "\n")
            row = [str(qc_report.get(col, "")) for col in concise_columns]
            f_out.write(",".join(row) + "\n")
        logging.info("Concise results written to %s", output_file)
        return

    # Legacy/simple behavior (e.g., unit tests): keep original, minimal writer
    sample_id_cols = [k for k in qc_report.keys() if k in ["Sample", "sample_id"]]
    all_checks_passed_cols = sorted([k for k in qc_report.keys() if k.endswith("all_checks_passed")])
    check_cols = sorted([k for k in qc_report.keys() if k.endswith(".check")])
    other_cols = sorted(
        [
            k
            for k in qc_report.keys()
            if k not in sample_id_cols
            and not k.endswith("all_checks_passed")
            and not k.endswith(".check")
        ]
    )
    ordered_keys = sample_id_cols + all_checks_passed_cols + check_cols + other_cols
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(",".join(ordered_keys) + "\n")
        f.write(",".join(str(qc_report[key]) for key in ordered_keys) + "\n")
        logging.info("Results written to %s", output_file)
