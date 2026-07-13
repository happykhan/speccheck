"""Backward-compatible workflow façade.

Workflow implementations live in focused modules. Imports from
``speccheck.main`` remain supported for existing users and scripts.
"""

import csv
import logging
import os

from speccheck.collect_workflow import (
    _add_parser_aliases,
    _filter_criteria_for_assembly_type,
    collect,
    collect_ghru,
)
from speccheck.summary_workflow import summary
from speccheck.update_criteria import QUALIBACT_DEFAULT_URL, update_criteria_file

__all__ = ["check", "collect", "collect_ghru", "summary"]


def check(criteria_file, update=False, update_url=QUALIBACT_DEFAULT_URL):
    """Validate the criteria CSV, optionally refreshing managed rows first."""
    logging.info("Checking criteria file: %s", criteria_file)
    errors = []
    if update:
        if update_criteria_file(criteria_file, update_url):
            logging.info("Updated criteria file from %s", update_url)
    if not os.path.isfile(criteria_file):
        logging.error("Criteria file not found: %s", criteria_file)
        return
    if not criteria_file.endswith(".csv"):
        errors.append("Criteria file is not a valid csv file.")

    required_columns = {
        "assembly_type",
        "software",
        "field",
        "operator",
        "value",
        "species",
        "special_field",
    }
    with open(criteria_file, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = required_columns.difference(reader.fieldnames or ())
        errors.extend(f"Missing required column: {column}" for column in sorted(missing_columns))
        has_baseline = any(row.get("species") == "all" for row in reader)

    if not has_baseline:
        errors.append("No criteria found for species 'all'.")
    for error in errors:
        logging.error(error)
    if not errors:
        logging.info("Criteria file is valid.")
