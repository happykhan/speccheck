import csv
import logging
import operator as op_from_module
import os
import re
from collections.abc import Iterable

from speccheck.report_tables import REPORT_SCHEMA_VERSION, combine_qc_statuses, status_label


def collect_files(all_files, module_list):
    # Execute checks for each file using discovered modules
    recovered_values = {}
    recovered_sources = {}
    for filepath in all_files:
        logging.debug("Checking %s", filepath)
        for module in module_list:
            current_module = module(filepath)
            if current_module.has_valid_filename and current_module.has_valid_fileformat:
                module_name = getattr(current_module, "software_name", module.__name__)
                logging.info("Detected %-10s %s", module_name, os.path.basename(filepath))
                if module_name in recovered_values:
                    previous = recovered_sources[module_name]
                    raise ValueError(
                        f"Multiple files matched parser {module_name}: {previous} and {filepath}. "
                        "Provide one output per parser for each sample, or split samples before collect."
                    )
                # Fetch values and criteria
                recovered_values[module_name] = current_module.fetch_values()
                recovered_sources[module_name] = filepath
    if not recovered_values:
        logging.warning("No files passed the checks.")
    return recovered_values


def criteria_applies_to_software(criteria_software, recovered_software):
    """Return True when a criteria row applies to a recovered parser output."""
    if criteria_software == recovered_software:
        return True
    return criteria_software.startswith("DepthParser") and recovered_software == "Depth"


def check_criteria(field, result):
    test_result = True
    software = field["software"]

    # --- Handle DepthParser hybrid output (short + long) ---
    # Depth.fetch_values returns a dict (single read type) or list (hybrid).
    if software.startswith("DepthParser"):
        # Determine which type of read (short or long) to check
        read_type = None
        if software.endswith(".short"):
            read_type = "short"
        elif software.endswith(".long"):
            read_type = "long"

        # If it's hybrid (list), pick the matching read type
        if isinstance(result, list):
            matched = next(
                (entry for entry in result if entry.get("Read_type", "").lower() == read_type), None
            )
            if not matched:
                logging.warning("No matching read type (%s) found for DepthParser", read_type)
                return False
            field_value = matched[field["field"]]
        else:
            # Single short or long file
            if read_type and result.get("Read_type", "").lower() != read_type:
                logging.warning("Depth row read type does not match criteria type (%s)", read_type)
                return False
            field_value = result[field["field"]]
    else:
        field_value = result[field["field"]]

    if field["operator"] == "regex":
        if not re.match(field["value"], str(field_value)):
            logging.warning(
                "Failed check for %s: %s does not match regex %s",
                field["software"],
                field["field"],
                field["value"],
            )
            test_result = False
    else:
        operator = field["operator"]
        criteria_value = field["value"]
        comparable_field_value = field_value

        if isinstance(criteria_value, (int, float)) and isinstance(field_value, str):
            stripped = field_value.strip()
            try:
                if "." in stripped or "e" in stripped.lower():
                    comparable_field_value = float(stripped)
                else:
                    comparable_field_value = int(stripped)
            except ValueError:
                logging.warning(
                    "Failed check for %s: %s value %r is not a numeric scalar for operator %s",
                    field["software"],
                    field["field"],
                    field_value,
                    field["operator"],
                )
                return False

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
        if not ops[operator](comparable_field_value, criteria_value):
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
    elif isinstance(raw, Iterable) and not isinstance(raw, (dict, bytes, bytearray)):
        parts = []
        for item in raw:
            if not item:
                continue
            parts.extend([p for p in str(item).split(";") if p])
    else:
        # Not a string or iterable of strings (e.g., numbers). Return as-is stringified.
        return str(raw)

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

    qc_report = dict(qc_report)
    looks_like_qc = any(
        key.startswith(
            (
                "Speciator.",
                "Depth.",
                "Sylph.",
                "Quast.",
                "Checkm.",
                "Fastp.",
                "Busco.",
                "Ariba.",
            )
        )
        for key in qc_report
    ) or ("sample_id" in qc_report and "all_checks_passed" in qc_report)
    if looks_like_qc:
        qc_report.setdefault(
            "speccheck_qc",
            status_label(qc_report.get("speccheck_overall_status"))
            or status_label(qc_report.get("all_checks_passed")),
        )
        for key, value in list(qc_report.items()):
            if key.endswith(".check"):
                qc_report.setdefault(key.removesuffix(".check") + ".status", status_label(value))

        for software in (
            "Speciator",
            "Depth",
            "Sylph",
            "Quast",
            "Checkm",
            "Fastp",
            "Busco",
            "Ariba",
        ):
            status_key = f"{software}.qc_status"
            if status_key in qc_report:
                continue
            metric_statuses = [
                value
                for key, value in qc_report.items()
                if key.startswith(f"{software}.") and key.endswith(".status")
            ]
            legacy_status = qc_report.get(f"{software}.all_checks_passed")
            qc_report[status_key] = combine_qc_statuses(legacy_status, *metric_statuses)

    def _format_cell(key, val):
        """Serialize every QC field with one status vocabulary."""
        if val is None:
            return ""

        if key.endswith(".check"):
            status_key = key.removesuffix(".check") + ".status"
            val = qc_report.get(status_key, val)
        key_is_status = (
            key.endswith("all_checks_passed")
            or key.endswith(".check")
            or key.endswith(".status")
            or key.endswith(".qc_status")
            or key.endswith("_qc")
        )
        if key_is_status:
            return status_label(val) or str(val)

        if isinstance(val, bool):
            return "YES" if val else "NO"

        # Default behaviour for everything else
        return str(val)

    # Columns required in concise output and their explicit order
    concise_columns = [
        "sample_id",
        "speccheck_qc",
        "Speciator.qc_status",
        "Speciator.speciesName",
        "Speciator.confidence",
        "Depth.qc_status",
        "Depth.Depth",
        "Depth.Read_type",
        "Sylph.qc_status",
        "Sylph.top_species",
        "Sylph.top_abundance_percent",
        "Sylph.top_sequence_abundance_percent",
        "Sylph.top_adjusted_ani",
        "Sylph.number_of_genomes",
        "Sylph.species_name",
        "Sylph.taxonomic_abundances_percent",
        "Sylph.sequence_abundances_percent",
        "Quast.qc_status",
        "Quast.# contigs (>= 0 bp).status",
        "Quast.# contigs (>= 0 bp)",
        "Quast.N50.status",
        "Quast.N50",
        "Quast.Total length (>= 0 bp).status",
        "Quast.Total length (>= 0 bp)",
        "Quast.GC (%).status",
        "Quast.GC (%)",
        "Quast.Largest contig",
        "Checkm.qc_status",
        "Checkm.Completeness.status",
        "Checkm.Completeness",
        "Checkm.Contamination.status",
        "Checkm.Contamination",
        "Checkm.GC_Content",
        "Checkm.Genome_Size",
        "Checkm.Contig_N50",
        "Checkm.Total_Contigs",
        "Checkm.Total_Coding_Sequences",
        "Fastp.qc_status",
        "Fastp.after_filtering_q30_rate.status",
        "Fastp.after_filtering_q30_rate",
        "Fastp.passed_filter_rate",
        "Fastp.duplication_rate",
        "Busco.qc_status",
        "Busco.Complete.status",
        "Busco.Complete",
        "Busco.Missing.status",
        "Busco.Missing",
        "Busco.Duplicated",
        "Busco.Fragmented",
        "Busco.Lineage",
        "Ariba.qc_status",
        "Ariba.percent.status",
        "Ariba.percent",
        "Ariba.passed",
        "Ariba.total",
        "Ariba.not_called",
        "Sylph.genomes",
        "report_schema_version",
    ]

    if looks_like_qc:
        qc_report["report_schema_version"] = REPORT_SCHEMA_VERSION
        # Sanitize Sylph.genomes to contain only accession IDs
        if "Sylph.genomes" in qc_report:
            qc_report = dict(qc_report)  # shallow copy to avoid mutating caller
            qc_report["Sylph.genomes"] = _extract_accessions_from_genome_paths(
                qc_report.get("Sylph.genomes")
            )
        # 1) Write detailed CSV (legacy, all fields) as detailed.<basename>
        detailed_dir = os.path.dirname(output_file)
        base = os.path.basename(output_file)
        detailed_path = (
            os.path.join(detailed_dir, f"detailed.{base}") if detailed_dir else f"detailed.{base}"
        )

        sample_id_cols = [k for k in qc_report.keys() if k in ["Sample", "sample_id"]]
        all_checks_passed_cols = sorted(
            [k for k in qc_report.keys() if k.endswith("all_checks_passed")]
        )
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

        with open(detailed_path, "w", encoding="utf-8", newline="") as f_det:
            writer = csv.DictWriter(f_det, fieldnames=detailed_keys)
            writer.writeheader()
            writer.writerow(
                {key: _format_cell(key, qc_report.get(key, "")) for key in detailed_keys}
            )
        logging.info("Detailed results written to %s", detailed_path)

        extra_status_columns = sorted(
            [key for key in qc_report if key.endswith(".status") and key not in concise_columns]
        )
        metadata_columns = sorted(
            [
                key
                for key in qc_report
                if key not in concise_columns
                and key not in extra_status_columns
                and key not in {"Sample", "sample_id", "all_checks_passed"}
                and "." not in key
            ]
        )
        concise_fieldnames = concise_columns + extra_status_columns + metadata_columns

        # 2) Write concise CSV with stable QC columns plus sample metadata.
        with open(output_file, "w", encoding="utf-8", newline="") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=concise_fieldnames)
            writer.writeheader()
            writer.writerow(
                {col: _format_cell(col, qc_report.get(col, "")) for col in concise_fieldnames}
            )
        logging.info("Concise results written to %s", output_file)
        return

    # Legacy/simple behavior (e.g., unit tests): keep original, minimal writer
    sample_id_cols = [k for k in qc_report.keys() if k in ["Sample", "sample_id"]]
    all_checks_passed_cols = sorted(
        [k for k in qc_report.keys() if k.endswith("all_checks_passed")]
    )
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
    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ordered_keys)
        writer.writeheader()
        writer.writerow({key: _format_cell(key, qc_report.get(key, "")) for key in ordered_keys})
        logging.info("Results written to %s", output_file)
