import os
import sys
import csv
import shutil
import logging
import pandas as pd
from speccheck.util import get_all_files, load_modules_with_checks
from speccheck.criteria import validate_criteria, get_species_field, get_criteria
from speccheck.report import plot_charts
from speccheck.collect import collect_files, write_to_file, check_criteria
from speccheck.update_criteria import update_criteria_file

def collect(organism, input_filepaths, criteria_file, output_file, sample_id, metadata_file=None):
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
    # Load metadata if provided
    metadata_dict = {}
    if metadata_file:
        if not os.path.isfile(metadata_file):
            logging.error("Metadata file not found: %s", metadata_file)
            return
        try:
            metadata_df = pd.read_csv(metadata_file)
            if 'sample_id' not in metadata_df.columns:
                logging.error("Metadata file must contain a 'sample_id' column")
                return
            metadata_df.set_index('sample_id', inplace=True)
            metadata_dict = metadata_df.to_dict('index')
            logging.info("Loaded metadata for %d samples from %s", len(metadata_dict), metadata_file)
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
        logging.warning("Organism name not provided and could not be resolved from the files. Using default values which are VERY lenient.")
        organism = 'Unknown'
    logging.info("Finished checking %d files for %s", len(all_files), organism)
    logging.info("Found software: %s", ', '.join(recovered_values.keys()))
    # get criteria
    criteria = get_criteria(criteria_file, organism)
    # run checks
    qc_report = {}  # dict to store results
    all_checks_passed = True
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
        qc_report[software + ".all_checks_passed"] = all_fields_passed
        all_checks_passed = all_checks_passed and all_fields_passed
    qc_report['all_checks_passed'] = all_checks_passed
    # log results
    # Write qc_report to file
    qc_report['sample_id'] = sample_id
    
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


def summary(directory, output, species, sample_id, template, plot = False):
    # TODO. CHECK ALL SAMPLE NAMES ARE UNIQUE
    os.makedirs(output, exist_ok=True)
    csv_files = []
    # collect all csv files
    for root, dirs, files in os.walk(directory):
        csv_files = [os.path.join(root, file) for file in files if file.endswith('.csv')]
    # merge all csv files in a single dictionary
    # TODO: Need to check all sample ids are unique, and sample_id column exists.
    merged_data = {}
    for file in csv_files:
        df = pd.read_csv(file)
        df.set_index(sample_id, inplace=True)
        merged_data.update(df.to_dict(orient='index'))
    # check if the sample field is present in the data
    if not merged_data:
        logging.error("No data found in the merged files.")
        return
    if any(pd.isna(sample_id) for sample_id in merged_data.keys()):
        logging.error("Sample names not found in the data.")
        return
    logging.info("Merged data for %d samples from %d files", len(merged_data), len(csv_files))
    # write merged data to a csv file
    output_file = os.path.join(output, 'report.csv')
    if plot: 
        plot_dict = merged_data.copy()
    
    # Collect all unique fieldnames
    all_fieldnames = set()
    for values in merged_data.values():
        all_fieldnames.update(values.keys())
    
    # Sort fieldnames: sample_id first, then .check columns, then alphabetically
    check_columns = sorted([col for col in all_fieldnames if col.endswith('.check')])
    other_columns = sorted([col for col in all_fieldnames if not col.endswith('.check')])
    fieldnames = ["sample_id"] + check_columns + other_columns
    
    # Sort merged_data by sample_id keys
    sorted_sample_ids = sorted(merged_data.keys())
    
    with open(output_file, 'w', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sample_id_key in sorted_sample_ids:
            values = merged_data[sample_id_key]
            row = {"sample_id": sample_id_key}
            row.update(values)
            writer.writerow(row)
            if plot:
                plot_dict[sample_id_key]["sample_id"] = sample_id_key
    # run plotting for each software (if available)
    if plot:
        plot_charts(plot_dict, species, output_html_path=os.path.join(output, 'report.html'), input_template_path=template)
        shutil.copy(os.path.join(os.path.dirname(template), 'bulma.css'), os.path.join(output, 'bulma.css'))
        logging.info("Plots generated.")

def check(criteria_file, update=False, update_url='https://raw.githubusercontent.com/happykhan/genomeqc/refs/heads/main/docs/summary/filtered_metrics.csv'):
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
