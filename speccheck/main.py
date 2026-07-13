import csv
import hashlib
import logging
import os
import sys

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
from speccheck.qualibact import add_qualibact_compatibility_columns
from speccheck.report import plot_charts
from speccheck.report_tables import (
    build_concise_report_frame,
    build_metric_summary_frames,
    export_summary_workbook,
    status_rank,
    status_label,
)
from speccheck.update_criteria import (
    QUALIBACT_DEFAULT_URL,
    get_threshold_source_for_species,
    update_criteria_file,
)
from speccheck.util import get_all_files, load_modules_with_checks


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
):
    """Collect and run checks from modules on input files."""
    # Check criteria file
    if not os.path.isfile(criteria_file):
        logging.error("Criteria file not found: %s", criteria_file)
        return
    errors, warnings = validate_criteria(criteria_file)
    if errors:
        for error in errors:
            logging.error("%s", error)
        sys.exit(1)
    if warnings:
        for warning in warnings:
            logging.warning("%s", warning)
    if not sample_id:
        logging.error("Sample name must be provided using --sample option.")
        return
    if assembly_type not in {"all", "short", "long", "hybrid"}:
        raise ValueError("assembly_type must be one of: all, short, long, hybrid")
    # Load metadata if provided
    metadata_dict = {}
    if metadata_file:
        if not os.path.isfile(metadata_file):
            logging.error("Metadata file not found: %s", metadata_file)
            return
        try:
            metadata_df = pd.read_csv(metadata_file)
            if "sample_id" not in metadata_df.columns:
                logging.error("Metadata file must contain a 'sample_id' column")
                return
            metadata_df.set_index("sample_id", inplace=True)
            metadata_dict = metadata_df.to_dict("index")
            logging.info(
                "Loaded metadata for %d samples from %s", len(metadata_dict), metadata_file
            )
        except Exception as e:
            logging.error("Error reading metadata file: %s", str(e))
            return

    # Get all files from the input paths
    all_files = get_all_files(input_filepaths)
    # Discover and load valid modules dynamically
    module_list = load_modules_with_checks()
    recovered_values = collect_files(all_files, module_list)
    if not recovered_values:
        logging.warning("No files passed the checks.")
        return
    _add_parser_aliases(recovered_values)

    # Need to resolve species if not provided
    org_list = []
    if not organism:
        species_fields = get_species_field(criteria_file)
        for field in species_fields:
            org_list.append(recovered_values.get(field["software"], {}).get(field["field"]))
        # remove None values
        org_list = [x for x in org_list if x is not None]
        organism = set(org_list)
        if len(organism) == 1:
            organism = list(organism)[0]
        elif len(organism) > 1:
            organism = None
            logging.error("Mixed species found in the files.")
        else:
            organism = None
    if not organism:
        message = (
            "Organism name was not provided and could not be resolved from parser outputs. "
            "Provide --organism or pass --allow-unknown-organism to use fallback criteria."
        )
        if not allow_unknown_organism:
            raise ValueError(message)
        logging.warning("%s Using fallback criteria for Unknown.", message)
        organism = "Unknown"
    logging.info("Finished checking %d files for %s", len(all_files), organism)
    logging.info("Found software: %s", ", ".join(recovered_values.keys()))
    # get criteria
    criteria_layers = get_criteria_layers(criteria_file, organism)
    baseline_criteria = _filter_criteria_for_assembly_type(criteria_layers["baseline"], assembly_type)
    species_criteria = _filter_criteria_for_assembly_type(criteria_layers["species"], assembly_type)
    # run checks
    qc_report = {}  # dict to store results
    all_checks_passed = True
    baseline_checks_passed = True
    species_checks_available = bool(species_criteria)
    species_checks_passed = True if species_checks_available else "NOT_AVAILABLE"
    not_evaluated_count = 0
    for software, result in recovered_values.items():
        logging.info("Running checks for %s", software)

        # ✅ Handle Depth hybrid output (list of dicts)
        if isinstance(result, list):
            for entry in result:
                read_type = entry.get("Read_type", "").lower()
                for res_name, res_value in entry.items():
                    if res_name in ("Read_type", "Sample_id"):
                        continue
                    col_name = f"{software}.{read_type}.{res_name}"
                    qc_report[col_name] = res_value
        else:
            for res_name, res_value in result.items():
                col_name = software + "." + res_name
                qc_report[col_name] = res_value

        baseline_result, baseline_not_evaluated = _evaluate_criteria_group(
            baseline_criteria,
            software,
            result,
            qc_report,
            fail_on_not_evaluated=fail_on_not_evaluated,
        )
        species_result, species_not_evaluated = _evaluate_criteria_group(
            species_criteria,
            software,
            result,
            qc_report,
            fail_on_not_evaluated=fail_on_not_evaluated,
        )
        not_evaluated_count += baseline_not_evaluated + species_not_evaluated

        qc_report[software + ".all_checks_passed"] = baseline_result and species_result
        all_checks_passed = all_checks_passed and qc_report[software + ".all_checks_passed"]
        baseline_checks_passed = baseline_checks_passed and baseline_result
        if species_checks_available:
            species_checks_passed = species_checks_passed and species_result
    qc_report["all_checks_passed"] = all_checks_passed
    qc_report["speccheck_baseline_checks_passed"] = baseline_checks_passed
    qc_report["speccheck_species_checks_passed"] = species_checks_passed
    qc_report["speccheck_species_checks_available"] = species_checks_available
    # log results
    # Write qc_report to file
    qc_report["sample_id"] = sample_id
    qc_report["speccheck_version"] = __version__
    qc_report["speccheck_assembly_type"] = assembly_type
    qc_report["speccheck_fail_on_not_evaluated"] = fail_on_not_evaluated
    qc_report["speccheck_criteria_file"] = os.path.abspath(criteria_file)
    qc_report["speccheck_criteria_sha256"] = _file_sha256(criteria_file)
    qc_report["speccheck_input_file_count"] = len(all_files)
    qc_report["speccheck_not_evaluated_count"] = not_evaluated_count
    threshold_source = get_threshold_source_for_species(organism)
    qc_report["speccheck_threshold_source"] = threshold_source["threshold_source"]
    qc_report["speccheck_threshold_scheme"] = threshold_source["scheme"]
    qc_report["speccheck_threshold_fallback_used"] = threshold_source["fallback_used"]

    # Merge metadata if available for this sample
    if metadata_file and sample_id in metadata_dict:
        logging.info("Merging metadata for sample: %s", sample_id)
        for meta_key, meta_value in metadata_dict[sample_id].items():
            qc_report[meta_key] = meta_value
    elif metadata_file and sample_id not in metadata_dict:
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
    sample_map = discover_ghru_sample_files(ghru_output_dir, work_dir=work_dir)
    selected_samples = sorted(sample_ids) if sample_ids else sorted(sample_map.keys())

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
        )
        written.append(output_file)

    logging.info("Wrote %d collected CSV file(s) to %s", len(written), os.path.abspath(output_dir))
    return written


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
        col_name = field["software"] + "." + field["field"] + ".check"
        if _result_has_field(result, field):
            test_result = check_criteria(field, result)
            group_passed = group_passed and test_result
            if col_name not in qc_report:
                qc_report[col_name] = test_result
            elif not test_result:
                qc_report[col_name] = test_result
        elif col_name not in qc_report:
            qc_report[col_name] = "NOT_EVALUATED"
            if fail_on_not_evaluated:
                group_passed = False
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
    """Add canonical aliases required by criteria without changing parser output names."""
    checkm = recovered_values.get("Checkm")
    if isinstance(checkm, dict):
        alias_map = {
            "GC_Content": "GC",
            "Genome_Size": "Genome size (bp)",
            "Contig_N50": "N50 (scaffolds)",
            "Total_Contigs": "# contigs",
        }
        for source, alias in alias_map.items():
            if source in checkm and alias not in checkm:
                checkm[alias] = checkm[source]


def summary(
    directory,
    output,
    species,
    sample_id,
    template,
    plot=False,
    xlsx_output=None,
    interactive_tables=True,
    qualifyr_style=False,
    qualibact_compat=False,
    qualibact_warn_as_fail=False,
):
    os.makedirs(output, exist_ok=True)
    csv_files = _discover_summary_csvs(directory, output)
    merged_data = _merge_summary_csvs(csv_files, sample_id)
    if not merged_data:
        logging.error("No data found in the merged files.")
        return
    if any(pd.isna(sample_id) for sample_id in merged_data.keys()):
        logging.error("Sample names not found in the data.")
        return
    logging.info("Merged data for %d samples from %d files", len(merged_data), len(csv_files))
    all_fieldnames = set()
    for values in merged_data.values():
        all_fieldnames.update(values.keys())
    check_columns = sorted([col for col in all_fieldnames if col.endswith(".check")])
    other_columns = sorted([col for col in all_fieldnames if not col.endswith(".check")])
    fieldnames = ["sample_id"] + check_columns + other_columns
    sorted_sample_ids = sorted(merged_data.keys())
    rows = []
    for sample_id_key in sorted_sample_ids:
        values = merged_data[sample_id_key]
        row = {"sample_id": sample_id_key}
        row.update(values)
        rows.append(row)

    report_df = pd.DataFrame(rows)
    report_df = report_df.reindex(columns=[col for col in fieldnames if col in report_df.columns])
    if qualibact_compat:
        report_df = add_qualibact_compatibility_columns(
            report_df,
            warn_as_fail=qualibact_warn_as_fail,
        )
        if qualibact_warn_as_fail:
            report_df["all_checks_passed"] = report_df["qualibact_compat_passed"]
        else:
            failed_mask = report_df["qualibact_compat_tier"] == "FAIL"
            report_df["all_checks_passed"] = report_df["all_checks_passed"].astype(object)
            report_df.loc[failed_mask, "all_checks_passed"] = False
    report_df = _decorate_report_dataframe(report_df)
    concise_report_df = build_concise_report_frame(report_df)
    normalized_full_df = _normalize_report_status_columns(report_df)
    normalized_concise_df = _normalize_report_status_columns(concise_report_df)

    plot_dict = {
        str(row["sample_id"]): row
        for row in report_df.to_dict(orient="records")
        if "sample_id" in row
    }
    concise_output = os.path.join(output, "report.csv")
    full_output = os.path.join(output, "report.full.csv")
    normalized_concise_df.to_csv(concise_output, index=False)
    normalized_full_df.to_csv(full_output, index=False)

    # run plotting for each software (if available)
    if plot:
        _report_df, summary_frames = plot_charts(
            plot_dict,
            species,
            output_html_path=os.path.join(output, "report.html"),
            input_template_path=template,
            interactive_tables=interactive_tables,
            qualifyr_style=qualifyr_style,
        )
        legacy_stylesheet = os.path.join(output, "bulma.css")
        if os.path.exists(legacy_stylesheet):
            os.remove(legacy_stylesheet)
        logging.info("Plots generated.")
    else:
        summary_frames = build_metric_summary_frames(report_df)

    if xlsx_output:
        export_summary_workbook(normalized_concise_df, normalized_full_df, xlsx_output, summary_frames)
        logging.info("Wrote XLSX summary to %s", xlsx_output)


def _discover_summary_csvs(directory, output):
    """Find summary input CSVs while ignoring generated artifacts."""
    csv_files = []
    skipped_detailed = []
    input_root = os.path.abspath(directory)
    output_root = os.path.abspath(output)

    for root, _dirs, files in os.walk(directory):
        abs_root = os.path.abspath(root)
        if abs_root == output_root or abs_root.startswith(output_root + os.sep):
            continue
        for file in files:
            if not file.endswith(".csv"):
                continue
            path = os.path.join(root, file)
            if file.startswith("detailed."):
                skipped_detailed.append(path)
                continue
            if os.path.abspath(path) in {
                os.path.join(output_root, "report.csv"),
                os.path.join(output_root, "report.full.csv"),
            }:
                continue
            csv_files.append(path)

    if skipped_detailed:
        logging.info(
            "Ignoring %d detailed CSV file(s) during summary merge; concise CSVs are used.",
            len(skipped_detailed),
        )
    if not csv_files:
        detail = " Only detailed.*.csv files were found." if skipped_detailed else ""
        raise ValueError(f"No summary input CSV files found under {input_root}.{detail}")
    return sorted(csv_files)


def _normalize_report_status_columns(report_df):
    """Write status-like report columns consistently as PASSED/FAILED/NOT_EVALUATED."""
    normalized = report_df.copy()
    status_columns = [
        column
        for column in normalized.columns
        if column.endswith(".check")
        or column.endswith("all_checks_passed")
        or column == "qualibact_compat_passed"
    ]
    for column in status_columns:
        normalized[column] = normalized[column].map(lambda value: status_label(value) or value)
    return normalized


def _decorate_report_dataframe(report_df):
    decorated = report_df.copy()
    decorated["overall_qc"] = decorated.apply(_row_overall_qc_label, axis=1)
    if "speccheck_baseline_checks_passed" in decorated.columns:
        decorated["baseline_qc"] = decorated["speccheck_baseline_checks_passed"]
    if "Speciator.speciesName" in decorated.columns and "species" not in decorated.columns:
        decorated["species"] = decorated["Speciator.speciesName"]
    if "Speciator.confidence" in decorated.columns and "species_confidence" not in decorated.columns:
        decorated["species_confidence"] = decorated["Speciator.confidence"]
    if "speccheck_threshold_source" in decorated.columns and "threshold_source" not in decorated.columns:
        decorated["threshold_source"] = decorated["speccheck_threshold_source"]
    decorated["reason_summary"] = decorated.apply(_row_reason_summary, axis=1)
    return decorated


def _row_overall_qc_label(row):
    compat_tier = row.get("qualibact_compat_tier")
    if pd.notna(compat_tier):
        return str(compat_tier)
    native_tier = row.get("qualibact_tier")
    if pd.notna(native_tier):
        return str(native_tier)
    return status_label(row.get("all_checks_passed")) or ""


def _row_reason_summary(row):
    for column in (
        "qualibact_reasons",
        "qualibact_compat_reasons",
    ):
        value = row.get(column)
        if pd.notna(value) and str(value).strip() and str(value).strip().lower() != "none":
            return str(value)

    reasons = []
    for column, value in row.items():
        if not column.endswith(".check"):
            continue
        if status_rank(value) == 0:
            reasons.append(column.removesuffix(".check"))
    return "; ".join(reasons[:5]) or "none"


def _merge_summary_csvs(csv_files, sample_id):
    """Merge sample CSVs and reject ambiguous sample identifiers."""
    merged_data = {}
    seen_samples = {}
    for file in csv_files:
        df = pd.read_csv(file)
        if sample_id not in df.columns:
            raise ValueError(
                f"Summary input {file} is missing required sample column '{sample_id}'."
            )
        if df[sample_id].isna().any():
            raise ValueError(f"Summary input {file} contains missing sample IDs in '{sample_id}'.")
        duplicated = df[df[sample_id].duplicated(keep=False)][sample_id].astype(str).tolist()
        if duplicated:
            raise ValueError(
                f"Summary input {file} contains duplicate sample IDs: {', '.join(sorted(set(duplicated)))}"
            )
        for row in df.to_dict(orient="records"):
            current_sample = str(row.pop(sample_id))
            if current_sample in seen_samples:
                raise ValueError(
                    f"Duplicate sample ID '{current_sample}' found in both "
                    f"{seen_samples[current_sample]} and {file}."
                )
            seen_samples[current_sample] = file
            merged_data[current_sample] = row
    return merged_data


def check(
    criteria_file,
    update=False,
    update_url=QUALIBACT_DEFAULT_URL,
):
    logging.info("Checking criteria file: %s", criteria_file)
    # Check criteria file if it has all the required fields
    # Use the 'all' species to template which fields are required
    errors = []
    warnings = []
    # if update is True, download the latest criteria file
    if update:
        update_criteria_file(criteria_file, update_url)
        logging.info("Updated criteria file from %s", update_url)
    # Check its a valid csv file
    if not os.path.isfile(criteria_file):
        logging.error("Criteria file not found: %s", criteria_file)
        return

    # check if the file is a valid csv file
    if not criteria_file.endswith(".csv"):
        errors.append("Criteria file is not a valid csv file.")

    # check if the file has the required fields
    columns = [
        "assembly_type",
        "software",
        "field",
        "operator",
        "value",
        "species",
        "special_field",
    ]
    with open(criteria_file, encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for column in columns:
            if column not in header:
                errors.append(f"Missing required column: {column}")

    with open(criteria_file, encoding="utf-8") as f:
        criteria = csv.DictReader(f)
        required = {}
        for row in criteria:
            required_name = row["assembly_type"] + "." + row["software"] + "." + row["field"]
            if row["species"] == "all":
                required[required_name] = {
                    "operator": row["operator"],
                    "value": row["value"],
                    "special_field": row["special_field"],
                }

    if not required:
        errors.append("No criteria found for species 'all'.")
    if warnings:
        for warning in warnings:
            logging.warning(warning)
    if errors:
        for error in errors:
            logging.error(error)
    if not errors or warnings:
        logging.info("Criteria file is valid.")
