"""
Collect and run checks from modules on input files.
This function takes an organism name and a list of input file paths,
collects all files from the given paths,
dynamically loads modules that contain checks, and runs these checks
on each file. It logs the progress and results of the checks.
Args:
    organism (str): The name of the organism for which the checks are being run.
    input_filepaths (list): A list of file paths to be checked.
Returns:
    None
"""

import os
import sys
import logging
import re
import csv
import operator as op_from_module
import pandas as pd
import matplotlib.pyplot as plt
from speccheck.util import get_all_files, load_modules_with_checks
from speccheck.criteria import validate_criteria, get_species_field, get_criteria
from speccheck.report import plot_charts

def collect(organism, input_filepaths, criteria_file, output_file, sample_name):
    """Collect and run checks from modules on input files."""
    # Check criteria file
    if not os.path.isfile(criteria_file):
        logging.error("Criteria file not found: %s", criteria_file)
        return
    errors, warnings = validate_criteria(criteria_file)
    if errors:
        for error in errors:
            logging.error(error)
        sys.exit(1)
    if warnings:
        for warning in warnings:
            logging.warning(warning)
    # Get all files from the input paths
    all_files = get_all_files(input_filepaths)
    print(all_files)
    # Discover and load valid modules dynamically
    module_list = load_modules_with_checks()

    # Execute checks for each file using discovered modules
    recovered_values = {}
    for filepath in all_files:
        logging.debug("Checking %s", filepath)
        for module in module_list:
            current_module = module(filepath)
            if (
                current_module.has_valid_filename
                and current_module.has_valid_fileformat
            ):
                logging.debug(
                    "File %s passed checks from %s", filepath, module.__name__
                )
                # Fetch values and criteria
                recovered_values[module.__name__] = current_module.fetch_values()
    if not recovered_values:
        logging.warning("No files passed the checks.")

    # Need to resolve species if not provided
    if not organism:
        species_fields = get_species_field(criteria_file)
        for field in species_fields:
            organism = recovered_values.get(field["software"], {}).get(field["field"])
    if not organism:
        logging.warning(
            "Organism name not provided and could not be resolved from the files. Using default values which are VERY leinient."
        )
    logging.info("Finished checking %d files for %s", len(all_files), organism)
    logging.info("Found software: %s", ", ".join(recovered_values.keys()))
    # get criteria
    criteria = get_criteria(criteria_file, organism)
    # run checks
    qc_report = {}  # dict to store results
    for software, result in recovered_values.items():
        logging.info("Running checks for %s", software)
        for res_name, res_value in result.items():
            col_name = software + "." + res_name
            qc_report[col_name] = res_value
        for field in criteria:
            if field["software"] == software:
                all_fields_passed = True
                if field["field"] in result:
                    test_result = True
                    print(field)
                    if field["operator"] == "regex":
                        if not re.match(field["value"], result[field["field"]]):
                            logging.warning(
                                "Failed check for %s: %s does not match regex %s",
                                field["software"],
                                field["field"],
                                field["value"],
                            )
                            test_result = False
                            all_fields_passed = False
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
                            all_fields_passed = False
                        col_name = field["software"] + "." + field["field"] + ".check"
                    if col_name not in qc_report:
                        qc_report[col_name] = test_result
                    elif not test_result:
                        qc_report[col_name] = test_result
                qc_report[field["software"] + ".all_checks_passed"] = all_fields_passed
    # log results
    # Write qc_report to file
    qc_report['Sample'] = sample_name
    logging.info("Writing results to file.")
    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        # write as csv where field is the column name and value is the value
        f.write(",".join(qc_report.keys()) + "\n")
        f.write(",".join(str(value) for value in qc_report.values()) + "\n")
        logging.info("Results written to %s", output_file)
    logging.info("All checks completed.")


def summary(directory, output, species, sample_name, plot = False):

    csv_files = []
    # collect all csv files
    for root, dirs, files in os.walk(directory):
        csv_files = [os.path.join(root, file) for file in files if file.endswith('.csv')]
    # merge all csv files in a single dictionary
    # TODO: Need to check all sample ids are unique, and sample_name column exists. 

    merged_data = {}
    for file in csv_files:
        df = pd.read_csv(file)
        df.set_index(sample_name, inplace=True)
        merged_data.update(df.to_dict(orient='index'))
    # write merged data to a csv file
    output_file = output + '.csv'
    with open(output_file, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["sample_name"] + list(next(iter(merged_data.values())).keys()))
        writer.writeheader()
        for sample_id, values in merged_data.items():
            row = {"sample_name": sample_id}
            row.update(values)
            writer.writerow(row)
    # run plotting for each software (if available)
    if plot:
        plot_charts(csv_files[0])

