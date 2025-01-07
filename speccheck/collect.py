import logging 
import os 
import operator as op_from_module
import re 

def collect_files(all_files, module_list):
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
    return recovered_values

def check_criteria(field, result):
    test_result = True
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

def write_to_file(output_file, qc_report):
    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        # write as csv where field is the column name and value is the value
        f.write(",".join(qc_report.keys()) + "\n")
        f.write(",".join(str(value) for value in qc_report.values()) + "\n")
        logging.info("Results written to %s", output_file)