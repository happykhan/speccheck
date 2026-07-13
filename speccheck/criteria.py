"""Criteria CSV validation and loading.

The runtime criteria file is deliberately plain CSV so thresholds can be
reviewed, cited, and replaced without changing Python code. Rows can be strict
failure thresholds or warning thresholds, and species-specific rows override
baseline rows for the same software/field pair.
"""

import csv
import logging
import os
import re

from speccheck.registry import get_parser_classes

REQUIRED_HEADERS = [
    "species",
    "assembly_type",
    "software",
    "field",
    "operator",
    "value",
    "special_field",
]
OPTIONAL_HEADERS = {"severity", "source"}
VALID_SEVERITIES = {"warn", "fail"}


def validate_criteria(criteria_file):
    """Return criteria CSV validation errors and warnings."""
    valid_software = {parser.software_name or parser.__name__ for parser in get_parser_classes()}
    valid_software.add("DepthParser")
    valid_operators = {">", "<", ">=", "<=", "=", "regex"}
    errors = []
    warnings = []

    # Check if file exists
    if not os.path.isfile(criteria_file):
        errors.append(f"File not found: {criteria_file}")
        return errors, warnings

    # Check if file is a valid CSV
    try:
        with open(criteria_file, encoding="utf-8") as f:
            csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
    except csv.Error:
        errors.append(f"File is not a valid CSV: {criteria_file}")
        return errors, warnings

    with open(criteria_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate headers
        fieldnames = reader.fieldnames or []
        missing_headers = [header for header in REQUIRED_HEADERS if header not in fieldnames]
        unexpected_headers = set(fieldnames).difference(REQUIRED_HEADERS, OPTIONAL_HEADERS)
        if missing_headers or unexpected_headers:
            errors.append(
                "Invalid headers. "
                f"Missing: {missing_headers or 'none'}; "
                f"unexpected: {sorted(unexpected_headers) or 'none'}"
            )
            return errors, warnings

        # Validate rows
        for i, row in enumerate(reader, start=2):
            # Validate required fields
            if not row["species"] or not row["software"] or not row["field"]:
                errors.append(f"Row {i}: Missing required fields")
                continue
            if not any(row["software"].startswith(name) for name in valid_software):
                warnings.append(f"Row {i}: Unsupported software '{row['software']}'")
            # Validate operator
            if row["operator"] not in valid_operators:
                errors.append(f"Row {i}: Invalid operator '{row['operator']}'")

            # Validate value based on operator
            if row["operator"] == "regex":
                try:
                    re.compile(row["value"])
                except re.error:
                    errors.append(f"Row {i}: Invalid regex pattern '{row['value']}'")
            else:
                try:
                    float(row["value"])
                except ValueError:
                    errors.append(
                        f"Row {i}: Value '{row['value']}' must be numeric for operator '{row['operator']}'"
                    )

            # Validate special_field if 'species_field'
            if "special_field" in row and row["special_field"] not in [
                "species_field",
                "",
            ]:
                warnings.append(
                    f"Row {i}: 'special_field' value is not supported: '{row['special_field']}'"
                )
            severity = row.get("severity", "fail").strip().lower() or "fail"
            if severity not in VALID_SEVERITIES:
                errors.append(
                    f"Row {i}: Invalid severity '{row.get('severity')}'. Expected warn or fail"
                )

    return errors, warnings


def get_species_field(criteria_file):
    """Return parser fields marked as organism/species inference fields."""
    rows = []

    with open(criteria_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        try:
            csv.Sniffer().sniff(f.read(2048))
            f.seek(0)
        except csv.Error as exc:
            raise csv.Error(f"File is not a valid CSV: {criteria_file}") from exc
        for row in reader:
            if row.get("special_field") == "species_field" and row.get("operator") == "regex":
                entry = {
                    "software": row.get("software"),
                    "field": row.get("field"),
                }
                # check if entry already in rows
                if entry not in rows:
                    rows.append(entry)
    return rows


def get_criteria(criteria_file, species=None):
    """Return baseline criteria plus optional species-specific criteria."""
    criteria = []
    with open(criteria_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        merge_criteria = []
        for row in reader:
            new_criteria = _normalize_criteria_row(row)

            if row["species"] == "all":
                criteria.append(new_criteria)
            if species and row["species"] == species:
                merge_criteria.append(new_criteria)
    if not species:
        return criteria
    if not merge_criteria:
        logging.warning(
            "No species-specific criteria found for %s. Using baseline criteria only.", species
        )
        return criteria
    return criteria + merge_criteria


def get_criteria_layers(criteria_file, species=None):
    """Return criteria split into baseline and species-specific layers."""
    baseline = []
    species_specific = []
    with open(criteria_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            new_criteria = _normalize_criteria_row(row)

            if row["species"] == "all":
                baseline.append(new_criteria)
            elif species and row["species"] == species:
                species_specific.append(new_criteria)
    overridden_metrics = {
        (criterion["software"], criterion["field"]) for criterion in species_specific
    }
    applicable_baseline = [
        criterion
        for criterion in baseline
        if (criterion["software"], criterion["field"]) not in overridden_metrics
    ]
    return {
        "baseline": applicable_baseline,
        "species": species_specific,
        "baseline_overridden_count": len(baseline) - len(applicable_baseline),
    }


def _normalize_criteria_row(row):
    value = row["value"]
    try:
        numeric = float(value)
        value = int(numeric) if numeric.is_integer() else numeric
    except ValueError:
        pass
    return {
        "assembly_type": row["assembly_type"],
        "software": row["software"],
        "field": row["field"],
        "operator": row["operator"],
        "value": value,
        "severity": row.get("severity", "fail").strip().lower() or "fail",
        "source": row.get("source", "custom").strip() or "custom",
        "special_field": row["special_field"],
    }
