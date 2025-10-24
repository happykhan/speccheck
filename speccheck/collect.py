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
            if current_module.has_valid_filename and current_module.has_valid_fileformat:
                logging.debug("File %s passed checks from %s", filepath, module.__name__)
                # Fetch values and criteria
                recovered_values[module.__name__] = current_module.fetch_values()
    if not recovered_values:
        logging.warning("No files passed the checks.")
    return recovered_values


def check_criteria(field, result):
    test_result = True
    software = field["software"]

    # --- Handle DepthParser hybrid output (short + long) ---
    # result["DepthParser"] can be a dict (short or long) or list (hybrid)
    if software.startswith("DepthParser"):
        # Determine which type of read (short or long) to check
        read_type = None
        if software.endswith(".short"):
            read_type = "short"
        elif software.endswith(".long"):
            read_type = "long"

        depth_entries = result.get("DepthParser")

        # If it's hybrid (list), pick the matching read type
        if isinstance(depth_entries, list):
            matched = next(
                (entry for entry in depth_entries if entry.get("Read_type") == read_type), None
            )
            if not matched:
                logging.warning("No matching read type (%s) found for DepthParser", read_type)
                return False
            field_value = matched[field["field"]]
        else:
            # Single short or long file
            field_value = depth_entries[field["field"]]
    else:
        field_value = result[field["field"]]

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

    # Order columns: sample_id, all_checks_passed columns, .check columns, then alphabetical
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

    with open(output_file, "w", encoding="utf-8") as f:
        # write as csv where field is the column name and value is the value
        f.write(",".join(ordered_keys) + "\n")
        f.write(",".join(str(qc_report[key]) for key in ordered_keys) + "\n")
        logging.info("Results written to %s", output_file)
