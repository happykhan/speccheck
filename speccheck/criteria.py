"""
This function checks if the criteria file is a
valid CSV file with the required headers and valid data.


    tuple: A tuple containing two lists:
        - errors (list): A list of error messages if the criteria file is invalid.
        - warnings (list): A list of warning messages for non-critical issues.
"""

import re
import os
import csv
import logging


def validate_criteria(criteria_file):
    """
    Validate the criteria file for processing.
    This function checks if the criteria file is a valid JSON file.
    Args:
        criteria_file (str): The path to the criteria file.
    Returns:
        bool: True if the criteria file is valid, False otherwise.
    """
    # Criteria file should be csv
    required_headers = [
        "species",
        "assembly_type",
        "software",
        "field",
        "operator",
        "value",
        "special_field",
    ]
    valid_software = ["Quast", "Checkm", "Speciator", 'Sylph', 'Ariba']
    valid_operators = {">", "<", ">=", "<=", "=", "regex"}
    errors = []
    warnings = []

    # Check if file exists
    if not os.path.isfile(criteria_file):
        errors.append(f"File not found: {criteria_file}")
        return errors, warnings

    # Check if file is a valid CSV
    try:
        with open(criteria_file, "r", encoding="utf-8") as f:
            csv.Sniffer().sniff(f.read(1024))
            f.seek(0)
    except csv.Error:
        errors.append(f"File is not a valid CSV: {criteria_file}")
        return errors, warnings

    with open(criteria_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate headers
        if reader.fieldnames != required_headers:
            errors.append(
                f"Invalid headers. Expected: {required_headers}, Found: {reader.fieldnames}"
            )
            return errors, warnings

        # Validate rows
        for i, row in enumerate(reader, start=2):
            # Validate required fields
            if not row["species"] or not row["software"] or not row["field"]:
                errors.append(f"Row {i}: Missing required fields")
                continue
            if row["software"] not in valid_software:
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

    return errors, warnings


def get_species_field(criteria_file):
    """
    Get the field name for the species.
    This function returns the field name for the species
    based on a predefined mapping.
    Args:
        species (str): The name of the species.
    Returns:
        str: The field name for the species.
    """
    rows = []
    
    with open(criteria_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        try:
            csv.Sniffer().sniff(f.read(2048))
            f.seek(0)
        except csv.Error as exc:
            raise csv.Error(f"File is not a valid CSV: {criteria_file}") from exc
        for row in reader:
            if (
                row.get("special_field") == "species_field"
                and row.get("operator") == "regex"
            ):
                entry = {
                    "software": row.get("software"),
                    "field": row.get("field"),
                }
                # check if entry already in rows
                if entry not in rows:
                    rows.append(entry)
    return rows


def get_criteria(criteria_file, species=None):
    """
    Get the criteria for a specific species.
    This function returns the criteria for a specific species
    based on the species name.
    Args:
        criteria_file (str): The path to the criteria file.
        species (str): The name of the species.
    Returns:
        dict: A dictionary of criteria for the species.
    """
    criteria = []
    with open(criteria_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        merge_criteria = []
        for row in reader:
            new_criteria = {
                "assembly_type": row["assembly_type"],
                "software": row["software"],
                "field": row["field"],
                "operator": row["operator"],
                "value": row["value"],
                "special_field": row["special_field"],
            }
            # A float will have a decimal point, so we try to convert the value to float
            if "." in new_criteria['value'] and new_criteria['value'].replace(".", "").isdigit():
                new_criteria['value'] = float(new_criteria['value'])
            # If the value is not a float, we try to convert it to an integer
            elif new_criteria['value'].isdigit():
                new_criteria['value'] = int(new_criteria['value'])

            if row["species"] == "all":
                criteria.append(new_criteria)
            if species and row["species"] == species:
                merge_criteria.append(new_criteria)
    for crit in criteria:
        found = False
        for merge in merge_criteria:
            # check if crit is missing from merge_criteria
            if (
                crit["assembly_type"] == merge["assembly_type"]
                and crit["software"] == merge["software"]
                and crit["field"] == merge["field"]
            ):
                found = True
        if not found:
            logging.warning(
                "Criteria for %s %s %s not found for species %s. Using default criteria.",
                crit["assembly_type"],
                crit["software"],
                crit["field"],
                species,
            )
            merge_criteria.append(crit)
    # return a list of dictionaries
    return merge_criteria
