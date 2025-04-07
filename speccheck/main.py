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
import csv
import pandas as pd
from speccheck.util import get_all_files, load_modules_with_checks
from speccheck.criteria import validate_criteria, get_species_field, get_criteria
from speccheck.report import plot_charts
from speccheck.collect import collect_files, write_to_file, check_criteria

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
    # Discover and load valid modules dynamically
    module_list = load_modules_with_checks()
    recovered_values = collect_files(all_files, module_list)
    if not recovered_values:
        logging.warning("No files passed the checks.")
        return

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

        all_fields_passed = True
        for field in criteria:
            if field["software"] == software:
                if field["field"] in result:
                    col_name = field["software"] + "." + field["field"] + ".check"
                    test_result = check_criteria(field, result)
                    all_fields_passed = all_fields_passed and test_result
                    if col_name not in qc_report:
                        qc_report[col_name] = test_result
                    elif not test_result:
                        qc_report[col_name] = test_result
        qc_report[field["software"] + ".all_checks_passed"] = all_fields_passed
    # log results
    # Write qc_report to file
    qc_report['Sample'] = sample_name
    logging.info("Writing results to file.")
    write_to_file(output_file, qc_report)
    logging.info("All checks completed.")


def summary(directory, output, species, sample_name, template, plot = False):

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
    # check if the sample field is present in the data
    if not merged_data:
        logging.error("No data found in the merged files.")
        return
    if any(pd.isna(sample_id) for sample_id in merged_data.keys()):
        logging.error("Sample names not found in the data.")
        return

    # write merged data to a csv file
    output_file = output + '.csv'
    if plot: 
        plot_dict = merged_data.copy()
    with open(output_file, 'w', encoding='utf-8') as f:
        fieldnames = ["sample_name"] + list(next(iter(merged_data.values())).keys())
        for sample_id, values in merged_data.items():
            for key in values.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sample_id, values in merged_data.items():
            row = {"sample_name": sample_id}
            row.update(values)
            writer.writerow(row)
            if plot:
                plot_dict[sample_id]["sample_name"] = sample_id
    # run plotting for each software (if available)
    if plot:
        plot_charts(plot_dict, species, output_html_path=output + '.html', input_template_path=template)
        logging.info("Plots generated.")

def check(criteria_file):
    logging.info("Checking criteria file: %s", criteria_file)
    # Check criteria file if it has all the required fields
    # Use the 'all' species to template which fields are required
    errors = []
    warnings = []
    # Check its a valid csv file
    if not os.path.isfile(criteria_file):
        logging.error("Criteria file not found: %s", criteria_file)
        return
    
    # check if the file is a valid csv file
    if not criteria_file.endswith('.csv'):
        errors.append("Criteria file is not a valid csv file.")
    
    # check if the file has the required fields
    columns = ['assembly_type', 'software', 'field', 'operator', 'value', 'species', 'special_field']
    with open(criteria_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for column in columns:
            if column not in header:
                errors.append(f"Missing required column: {column}")

    with open(criteria_file, 'r', encoding='utf-8') as f:
        criteria = csv.DictReader(f)
        required = {} 
        species_rules = {}
        for row in criteria:
            required_name = row['assembly_type'] + '.' + row['software'] + '.' + row['field']
            if row['species'] == 'all':
                required[required_name] = {'operator': row['operator'], 'value': row['value'], 'special_field': row['special_field']}
            else:
                if row['species'] in species_rules:
                    species_rules[row['species']].append({required_name: {'operator': row['operator'], 'value': row['value'], 'special_field': row['special_field']}})
                else:
                    species_rules[row['species']] = [{required_name: {'operator': row['operator'], 'value': row['value'], 'special_field': row['special_field']}}]

        for species, rules in species_rules.items():
            for field, rule in required.items():
                if field not in [list(x.keys())[0] for x in rules]:
                    errors.append(f"Required field {field} not found for species {species}. 'all' value is {rule['operator']} {rule['value']} {rule['special_field']}")
        

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