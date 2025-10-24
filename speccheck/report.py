import os
import importlib
import logging
import pandas as pd
from jinja2 import Template
from speccheck import __version__ as VERSION


def make_sample_counts(df):
    """
    Generates a summary of sample counts for each software module.

    Parameters:
    df (DataFrame): DataFrame containing QC check results with columns ending in 'all_checks_passed'.

    Returns:
    dict: Dictionary with software names as keys and sample counts as values.
    """
    # Count total samples, passes, and fails
    sum_table = _get_sum_table(df)
    total_samples = len(sum_table)
    pass_count = sum_table["QC_PASS"].value_counts().get("Pass", 0)
    fail_count = sum_table["QC_PASS"].value_counts().get("Fail", 0)
    pass_percentage = (pass_count / total_samples) * 100 if total_samples > 0 else 0
    sample_counts = {}
    for col in df.columns:
        if col.endswith("all_checks_passed"):
            software_name = col.split(".")[0]
            sample_counts[software_name] = df[col].count()
    text = (
        f"There are {total_samples} samples included with "
        f"<span style='color:green'>{pass_count} passing</span> and "
        f"<span style='color:red'>{fail_count} failing</span> "
        f"({pass_percentage:.2f}% pass rate)."
    )
    return text


def _get_sum_table(df):
    # Select columns ending with 'all_checks_passed'
    sum_table = df[[col for col in df.columns if col.endswith("all_checks_passed")]]
    # Create a new column 'QC_PASS' that is True if all checks passed
    sum_table["QC_PASS"] = sum_table.all(axis=1)

    # Change True/False to Pass/Fail
    sum_table = sum_table.replace({True: "Pass", False: "Fail"})

    # Rename columns to remove the '.all_checks_passed' suffix
    sum_table.columns = sum_table.columns.str.replace(".all_checks_passed", "", regex=False)
    return sum_table


def summary_table(df):
    """
    Generates an HTML summary table with QC results, including explanatory text.

    Parameters:
    df (DataFrame): DataFrame containing QC check results with columns ending in 'all_checks_passed'.
    software_modules (list): List of software modules available for plotting.

    Returns:
    str: HTML string containing the styled summary table with explanatory text.
    """
    sum_table = _get_sum_table(df)

    # Define a function to apply color styling
    def colorize(val):
        if val == "Fail":
            return "background-color: #FFC8C8; color: black;"
        elif val == "Pass":
            return "background-color: #90EE90; color: black;"
        return ""

    # Apply the styling function to the DataFrame

    styled_table = sum_table.style.applymap(colorize).set_table_attributes(
        'class="table is-striped is-fullwidth"'
    )
    # Convert the styled DataFrame to HTML
    table_html = styled_table.to_html(escape=False)
    # Construct explanatory text
    explanation = """
    <p>This table shows the results of the quality control checks. Each row represents a sample, and each column represents a check. The last column indicates whether all checks passed for that sample.</p>
    """
    # Combine explanation and table
    full_html = explanation + '<div class="table-container">' + table_html + "</div>"

    return full_html


def make_footer():
    """
    Generates an HTML footer indicating the report was produced with speccheck.

    Returns:
        str: An HTML string containing a link to the speccheck repository and the current version.
    """
    return f'<p>Produced with <a href="https://github.com/happykhan/speccheck">speccheck</a> version {VERSION}</p>'


def load_modules_with_checks():
    """Load Python modules with required checks from the 'plot_modules' directory."""
    module_dict = {}
    modules_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plot_modules")

    for filename in os.listdir(modules_file_path):
        if not filename.endswith(".py"):
            continue

        curr_module_path = os.path.join(modules_file_path, filename)
        if not os.path.isfile(curr_module_path):
            continue

        module_name = os.path.splitext(filename)[0]
        spec = importlib.util.spec_from_file_location(module_name, curr_module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class_name = module_name.title()
        if hasattr(module, class_name):
            cla = getattr(module, class_name)
            if hasattr(cla, "plot"):
                module_dict[class_name.split("_")[1]] = cla

    loaded_classes = ", ".join([cls.__name__ for cls in module_dict.values()])
    logging.debug("Loaded modules: %s", loaded_classes)
    return module_dict


def get_software_summary(software_dict):
    """
    Generates a summary of software modules with their names, descriptions, versions, and URLs.

    Parameters:
    software_dict (dict): Dictionary containing software module information.

    Returns:
    str: HTML string containing the software summary.
    """
    summary = "<p>Software that were included: </p>"
    # Write software description list based on contents of software
    software_list = "<ul>"
    for soft in software_dict.values():
        software_list += (
            f"<li><b><a href=#{soft['name'].lower()}>{soft['name']}</a></b>: {soft['description']} "
        )
        if soft["url"]:
            software_list += f' (<a href="{soft["url"]}">website</a>)'
        if soft.get("version"):
            software_list += f" (version: {soft['version']})"
        if soft.get("citation"):
            software_list += f' (<a href="{soft["citation"]}">ref</a>)'
        software_list += "</li>"
    summary += software_list
    summary += "</ul>"
    return summary


def get_failure_reasons(df, software_dict):
    """
    Generates a summary of failure reasons for the report.

    Returns:
    str: HTML string containing the failure reasons.
    """
    sum_table = _get_sum_table(df)
    # Identify the top 5 reasons for failure
    # This assumes that a 'Fail' in any column (except 'QC_PASS') contributes to the failure reason
    failure_reasons = (
        sum_table[sum_table["QC_PASS"] == "Fail"]
        .drop(columns=["QC_PASS"])
        .apply(lambda x: x == "Fail")
    )
    explanation = ""
    top_failure_reasons = failure_reasons.sum().sort_values(ascending=False).head(5)
    # remove reasons that have less than 1 failure
    top_failure_reasons = top_failure_reasons[top_failure_reasons > 0]
    failure_string = ""
    if len(top_failure_reasons) == 1:
        failure_string = "<p>This was the top reason for failure:</p>"
    elif len(top_failure_reasons) > 1:
        failure_string = (
            f"<p>These were the top {len(top_failure_reasons)} reasons for failure:</p>"
        )
    if len(top_failure_reasons) > 0:
        explanation += failure_string
        explanation += "<ol>"
        for reason, count in top_failure_reasons.items():
            if reason not in software_dict:
                logging.warning("No software found for reason: %s", reason)
                continue
            name = software_dict.get(reason)["name"]
            explanation += f"<li><b><a href=#{name.lower()}>{name}</a></b>: {count} failures</li>"
        explanation += "</ol>"
    return explanation


def plot_charts(
    merged_dict,
    species,
    output_html_path="yes.html",
    input_template_path="templates/report.html",
):
    """
    Generates an HTML report with charts and summary tables based on the provided merged data.

    This function processes a dictionary of sample data, organizes it by software modules,
    generates summary statistics and plots for each module, and renders the results into an
    HTML file using a Jinja2 template.

    Args:
        merged_dict (dict): A dictionary where each key is a sample identifier and each value is a
            dictionary of sample attributes and results.
        species (str): The name of the column in the data that contains species information.
        output_html_path (str, optional): Path to the output HTML file. Defaults to "yes.html".
        input_template_path (str, optional): Path to the Jinja2 HTML template file. Defaults to "templates/report.html".

    Returns:
        None: Writes the rendered HTML report to the specified output path.

    Side Effects:
        - Writes an HTML file to `output_html_path`.
        - Logs warnings and errors if modules are missing or required data is absent.

    Raises:
        None explicitly, but may raise exceptions if file operations or template rendering fails.
    """
    software_modules = load_modules_with_checks()
    plotly_jinja_data = {"software_charts": ""}
    # make sure sample_id has a value, if its nan, just put sample01 ... sampleN
    for idx, (key, value) in enumerate(merged_dict.items(), start=1):
        if not isinstance(value, dict):
            merged_dict[key] = {}
        if "sample_id" not in merged_dict[key] or pd.isna(merged_dict[key]["sample_id"]):
            merged_dict[key]["sample_id"] = f"sample{idx}"
    # convert the dictionary to a pandas dataframe
    df = pd.DataFrame.from_dict(merged_dict, orient="index")
    # Remove column all_checks_passed if it exists
    if "all_checks_passed" in df.columns:
        df.drop(columns=["all_checks_passed"], inplace=True)
    # split columns into groups based on the column name before the first dot
    groups = df.columns.to_series().str.split(".").str[0]
    # seperate each group into a new dataframe
    unique_groups = groups.unique()
    unique_groups = unique_groups[unique_groups != "sample_id"]
    software_dict = {}
    # Species might not be present in the data, if so, add it with value 'Unknown'
    if species not in df.columns:
        df[species] = "Unknown"
    for software in unique_groups:
        # Also include species column in the group
        group_df = df[[col for col in df.columns if col.startswith(software)]]
        # TODO: Species column is a protected column in this case.
        # Need to make sure it doesn't exist prior.
        group_df = group_df.join(df[species].rename("species"))
        group_df.columns = group_df.columns.str.replace(f"{software}.", "", regex=False)
        if software in software_modules:
            software_obj = software_modules[software](group_df)
            software_dict[software] = software_obj.summary()
            plotly_jinja_data["software_charts"] += software_obj.plot()
        else:
            logging.warning("No plot module found for %s. Skipping plotting.", software)
    plotly_jinja_data["sample_count"] = make_sample_counts(df)
    plotly_jinja_data["footer"] = make_footer()
    plotly_jinja_data["summary_table"] = summary_table(df)
    plotly_jinja_data["software_summary"] = get_software_summary(software_dict)
    plotly_jinja_data["failure_reasons"] = get_failure_reasons(df, software_dict)
    required_keys = [
        "software_charts",
        "summary_table",
        "footer",
        "sample_count",
        "software_summary",
        "failure_reasons",
    ]
    plotly_jinja_data["version"] = VERSION
    for key in required_keys:
        if key not in plotly_jinja_data:
            logging.error("Missing required key in plotly_jinja_data: %s", key)
            return None
    with open(output_html_path, "w", encoding="utf-8") as output_file:
        with open(input_template_path, encoding="utf-8") as template_file:
            j2_template = Template(template_file.read())
            output_file.write(j2_template.render(plotly_jinja_data))
