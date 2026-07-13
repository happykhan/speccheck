"""Collection workflow: parse one sample and evaluate applicable criteria."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from dataclasses import dataclass, field

import pandas as pd

from speccheck import __version__
from speccheck.collect import (
    check_criteria,
    collect_files,
    criteria_applies_to_software,
    write_to_file,
)
from speccheck.criteria import get_criteria_layers, get_species_field, validate_criteria
from speccheck.ghru import discover_ghru_sample_files
from speccheck.registry import add_metric_aliases
from speccheck.update_criteria import get_threshold_source_for_species
from speccheck.util import get_all_files, load_modules_with_checks

ASSEMBLY_TYPES = frozenset({"all", "short", "long", "hybrid"})


@dataclass
class CollectionContext:
    """Run-scoped immutable inputs plus small lookup caches."""

    criteria_file: str
    criteria_sha256: str
    metadata: dict
    species_fields: list[dict]
    criteria_layers: dict[str, dict] = field(default_factory=dict)
    threshold_sources: dict[str, dict] = field(default_factory=dict)


def collect(
    organism,
    input_filepaths,
    criteria_file,
    output_file,
    sample_id,
    metadata_file=None,
    allow_unknown_organism=False,
    assembly_type="short",
    fail_on_not_evaluated=False,
    _context=None,
):
    """Collect parser values, evaluate criteria, and write one sample report."""
    _validate_sample_request(sample_id, assembly_type)
    context = _context or _prepare_collection_context(criteria_file, metadata_file)
    if os.path.abspath(criteria_file) != context.criteria_file:
        raise ValueError("Collection context criteria file does not match the requested criteria file")
    all_files = get_all_files(input_filepaths)
    recovered_values = collect_files(all_files, load_modules_with_checks())
    if not recovered_values:
        logging.warning("No files passed the checks.")
        return
    _add_parser_aliases(recovered_values)

    organism = _resolve_organism(
        organism,
        recovered_values,
        context.species_fields,
        allow_unknown=allow_unknown_organism,
    )
    logging.info("Finished checking %d files for %s", len(all_files), organism)
    logging.info("Found software: %s", ", ".join(recovered_values))

    criteria_layers = _criteria_layers_for(context, organism)
    baseline_criteria = _filter_criteria_for_assembly_type(
        criteria_layers["baseline"], assembly_type
    )
    species_criteria = _filter_criteria_for_assembly_type(
        criteria_layers["species"], assembly_type
    )
    qc_report = _evaluate_sample(
        recovered_values,
        baseline_criteria,
        species_criteria,
        fail_on_not_evaluated=fail_on_not_evaluated,
    )
    qc_report.update(
        _collection_provenance(
            sample_id=sample_id,
            organism=organism,
            assembly_type=assembly_type,
            criteria_file=criteria_file,
            criteria_sha256=context.criteria_sha256,
            input_file_count=len(all_files),
            not_evaluated_count=qc_report.pop("_not_evaluated_count"),
            fail_on_not_evaluated=fail_on_not_evaluated,
            threshold_source=_threshold_source_for(context, organism),
        )
    )
    if metadata_file and sample_id in context.metadata:
        logging.info("Merging metadata for sample: %s", sample_id)
        qc_report.update(context.metadata[sample_id])
    elif metadata_file:
        logging.warning("No metadata found for sample: %s", sample_id)

    logging.info("Writing results to file.")
    write_to_file(output_file, qc_report)
    logging.info("All checks completed.")


def collect_ghru(
    ghru_output_dir,
    output_dir,
    criteria_file,
    organism=None,
    metadata_file=None,
    allow_unknown_organism=False,
    fail_on_not_evaluated=False,
    work_dir=None,
    sample_ids=None,
):
    """Collect one CSV per sample directly from a GHRU output directory."""
    os.makedirs(output_dir, exist_ok=True)
    context = _prepare_collection_context(criteria_file, metadata_file)
    sample_map = discover_ghru_sample_files(ghru_output_dir, work_dir=work_dir)
    selected_samples = sorted(sample_ids) if sample_ids else sorted(sample_map)
    missing_samples = [sample_id for sample_id in selected_samples if sample_id not in sample_map]
    if missing_samples:
        raise ValueError(
            "Requested sample(s) were not found in the GHRU output tree: "
            + ", ".join(missing_samples)
        )

    written = []
    for sample_id in selected_samples:
        sample = sample_map[sample_id]
        if not sample.assembly_type:
            raise ValueError(f"Could not infer assembly type for sample {sample_id}")
        output_file = os.path.join(output_dir, f"{sample_id}.csv")
        logging.info(
            "Collecting GHRU outputs for %s (%s assembly) from %d file(s)",
            sample_id,
            sample.assembly_type,
            len(sample.files),
        )
        collect(
            organism,
            sample.files,
            criteria_file,
            output_file,
            sample_id,
            metadata_file=metadata_file,
            allow_unknown_organism=allow_unknown_organism,
            assembly_type=sample.assembly_type,
            fail_on_not_evaluated=fail_on_not_evaluated,
            _context=context,
        )
        written.append(output_file)

    logging.info("Wrote %d collected CSV file(s) to %s", len(written), os.path.abspath(output_dir))
    return written


def _prepare_collection_context(criteria_file, metadata_file=None):
    if not os.path.isfile(criteria_file):
        raise FileNotFoundError(f"Criteria file not found: {criteria_file}")
    errors, warnings = validate_criteria(criteria_file)
    for warning in warnings:
        logging.warning("%s", warning)
    if errors:
        for error in errors:
            logging.error("%s", error)
        sys.exit(1)
    absolute_criteria_file = os.path.abspath(criteria_file)
    return CollectionContext(
        criteria_file=absolute_criteria_file,
        criteria_sha256=_file_sha256(absolute_criteria_file),
        metadata=_load_metadata(metadata_file),
        species_fields=get_species_field(absolute_criteria_file),
    )


def _validate_sample_request(sample_id, assembly_type):
    if not sample_id:
        raise ValueError("Sample name must be provided using --sample.")
    if assembly_type not in ASSEMBLY_TYPES:
        raise ValueError("assembly_type must be one of: all, short, long, hybrid")


def _load_metadata(metadata_file):
    if not metadata_file:
        return {}
    if not os.path.isfile(metadata_file):
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")
    metadata_df = pd.read_csv(metadata_file)
    if "sample_id" not in metadata_df.columns:
        raise ValueError("Metadata file must contain a 'sample_id' column")
    if metadata_df["sample_id"].duplicated().any():
        raise ValueError("Metadata file contains duplicate sample_id values")
    metadata_df.set_index("sample_id", inplace=True)
    logging.info("Loaded metadata for %d samples from %s", len(metadata_df), metadata_file)
    return metadata_df.to_dict("index")


def _resolve_organism(organism, recovered_values, species_fields, *, allow_unknown):
    if organism:
        return organism
    candidates = {
        recovered_values.get(field["software"], {}).get(field["field"])
        for field in species_fields
        if isinstance(recovered_values.get(field["software"]), dict)
    }
    candidates.discard(None)
    if len(candidates) == 1:
        return candidates.pop()
    if len(candidates) > 1:
        logging.error("Mixed species found in the files: %s", ", ".join(sorted(candidates)))
    message = (
        "Organism name was not provided and could not be resolved from parser outputs. "
        "Provide --organism or pass --allow-unknown-organism to use fallback criteria."
    )
    if not allow_unknown:
        raise ValueError(message)
    logging.warning("%s Using fallback criteria for Unknown.", message)
    return "Unknown"


def _evaluate_sample(
    recovered_values,
    baseline_criteria,
    species_criteria,
    *,
    fail_on_not_evaluated,
):
    qc_report = {}
    baseline_checks_passed = True
    species_checks_available = bool(species_criteria)
    species_checks_passed = True if species_checks_available else "NOT_AVAILABLE"
    not_evaluated_count = 0

    for software, result in recovered_values.items():
        logging.info("Running checks for %s", software)
        _add_parsed_values(qc_report, software, result)
        baseline_result, baseline_missing = _evaluate_criteria_group(
            baseline_criteria,
            software,
            result,
            qc_report,
            fail_on_not_evaluated=fail_on_not_evaluated,
        )
        species_result, species_missing = _evaluate_criteria_group(
            species_criteria,
            software,
            result,
            qc_report,
            fail_on_not_evaluated=fail_on_not_evaluated,
        )
        not_evaluated_count += baseline_missing + species_missing
        qc_report[f"{software}.all_checks_passed"] = baseline_result and species_result
        baseline_checks_passed = baseline_checks_passed and baseline_result
        if species_checks_available:
            species_checks_passed = species_checks_passed and species_result

    parser_statuses = [
        value for key, value in qc_report.items() if key.endswith(".all_checks_passed")
    ]
    qc_report["all_checks_passed"] = all(parser_statuses)
    qc_report["speccheck_baseline_checks_passed"] = baseline_checks_passed
    qc_report["speccheck_species_checks_passed"] = species_checks_passed
    qc_report["speccheck_species_checks_available"] = species_checks_available
    qc_report["_not_evaluated_count"] = not_evaluated_count
    return qc_report


def _add_parsed_values(qc_report, software, result):
    if isinstance(result, list):
        for entry in result:
            read_type = entry.get("Read_type", "").lower()
            for name, value in entry.items():
                if name not in {"Read_type", "Sample_id"}:
                    qc_report[f"{software}.{read_type}.{name}"] = value
        return
    for name, value in result.items():
        qc_report[f"{software}.{name}"] = value


def _collection_provenance(
    *,
    sample_id,
    organism,
    assembly_type,
    criteria_file,
    criteria_sha256,
    input_file_count,
    not_evaluated_count,
    fail_on_not_evaluated,
    threshold_source,
):
    return {
        "sample_id": sample_id,
        "speccheck_version": __version__,
        "speccheck_assembly_type": assembly_type,
        "speccheck_fail_on_not_evaluated": fail_on_not_evaluated,
        "speccheck_criteria_file": os.path.abspath(criteria_file),
        "speccheck_criteria_sha256": criteria_sha256,
        "speccheck_input_file_count": input_file_count,
        "speccheck_not_evaluated_count": not_evaluated_count,
        "speccheck_threshold_source": threshold_source["threshold_source"],
        "speccheck_threshold_scheme": threshold_source["scheme"],
        "speccheck_threshold_fallback_used": threshold_source["fallback_used"],
    }


def _criteria_layers_for(context, organism):
    if organism not in context.criteria_layers:
        context.criteria_layers[organism] = get_criteria_layers(context.criteria_file, organism)
    return context.criteria_layers[organism]


def _threshold_source_for(context, organism):
    if organism not in context.threshold_sources:
        context.threshold_sources[organism] = get_threshold_source_for_species(organism)
    return context.threshold_sources[organism]


def _result_has_field(result, field):
    field_name = field["field"]
    software = field["software"]
    if software.startswith("DepthParser"):
        expected_read_type = software.rsplit(".", 1)[-1].lower() if "." in software else None
        if isinstance(result, list):
            return any(
                entry.get("Read_type", "").lower() == expected_read_type and field_name in entry
                for entry in result
            )
        return result.get("Read_type", "").lower() == expected_read_type and field_name in result
    if isinstance(result, list):
        return any(field_name in entry for entry in result)
    return field_name in result


def _evaluate_criteria_group(
    criteria,
    software,
    result,
    qc_report,
    *,
    fail_on_not_evaluated=False,
):
    group_passed = True
    not_evaluated_count = 0
    for field in criteria:
        if not criteria_applies_to_software(field["software"], software):
            continue
        column = f'{field["software"]}.{field["field"]}.check'
        if _result_has_field(result, field):
            test_result = check_criteria(field, result)
            group_passed = group_passed and test_result
            qc_report[column] = qc_report.get(column, True) and test_result
        elif column not in qc_report:
            qc_report[column] = "NOT_EVALUATED"
            group_passed = group_passed and not fail_on_not_evaluated
            not_evaluated_count += 1
            logging.warning(
                "Criteria field %s.%s was not evaluated because the parsed %s output did not contain that metric.",
                field["software"],
                field["field"],
                software,
            )
    return group_passed, not_evaluated_count


def _filter_criteria_for_assembly_type(criteria, assembly_type):
    """Keep criteria rows that apply to the requested assembly type."""
    allowed = {"all"}
    if assembly_type in {"short", "long"}:
        allowed.add(assembly_type)
    elif assembly_type == "hybrid":
        allowed.update({"short", "long"})
    return [field for field in criteria if field.get("assembly_type", "all") in allowed]


def _file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _add_parser_aliases(recovered_values):
    """Add registered metric aliases without changing parser ownership."""
    for software, values in recovered_values.items():
        if isinstance(values, dict):
            add_metric_aliases(values, software)
