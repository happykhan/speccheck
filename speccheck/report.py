import os
import importlib
import logging
import pandas as pd
from jinja2 import Template

def summary_table(df):
    """
    Generates an HTML summary table with QC results, including explanatory text.

    Parameters:
    df (DataFrame): DataFrame containing QC check results with columns ending in 'all_checks_passed'.

    Returns:
    str: HTML string containing the styled summary table with explanatory text.
    """
    # Select columns ending with 'all_checks_passed'
    sum_table = df[[col for col in df.columns if col.endswith("all_checks_passed")]]
    
    # Create a new column 'QC_PASS' that is True if all checks passed
    sum_table["QC_PASS"] = sum_table.all(axis=1)
    
    # Change True/False to Pass/Fail
    sum_table = sum_table.replace({True: "Pass", False: "Fail"})
    
    # Rename columns to remove the '.all_checks_passed' suffix
    sum_table.columns = sum_table.columns.str.replace(".all_checks_passed", "", regex=False)
    
    # Count total samples, passes, and fails
    total_samples = len(sum_table)
    pass_count = sum_table["QC_PASS"].value_counts().get("Pass", 0)
    fail_count = sum_table["QC_PASS"].value_counts().get("Fail", 0)
    pass_percentage = (pass_count / total_samples) * 100 if total_samples > 0 else 0
    
    # List of software included (derived from column names)
    software_included = ", ".join(sum_table.columns[:-1])
    
    # Identify the top 5 reasons for failure
    # This assumes that a 'Fail' in any column (except 'QC_PASS') contributes to the failure reason
    failure_reasons = sum_table[sum_table["QC_PASS"] == "Fail"].drop(columns=["QC_PASS"]).apply(lambda x: x == "Fail")
    top_failure_reasons = failure_reasons.sum().sort_values(ascending=False).head(5)
    
    # Define a function to apply color styling
    def colorize(val):
        if val == "Fail":
            return 'background-color: #FFC8C8; color: black;'
        elif val == "Pass":
            return 'background-color: #90EE90; color: black;'
        return ''
    
    # Apply the styling function to the DataFrame
    styled_table = sum_table.style.applymap(colorize)
    
    # Convert the styled DataFrame to HTML
    table_html = styled_table.to_html(escape=False)
    
    # Construct explanatory text
    explanation = f"""
    <p>This table shows the results of the quality control checks. Each row represents a sample, and each column represents a check. The last column indicates whether all checks passed for that sample.</p>
    <p>There are {total_samples} samples included with {pass_count} passing and {fail_count} failing ({pass_percentage:.2f}% pass rate).</p>
    <p>Software that were included: {software_included}</p>
    <p>These were the top 5 reasons for failure:</p>
    <ol>
    """
    for reason, count in top_failure_reasons.items():
        explanation += f"<li>{reason}: {count} failures</li>"
    explanation += "</ol>"
    
    # Combine explanation and table
    full_html = explanation + table_html
    
    return full_html



def plot_charts(merged_dict, species, output_html_path='yes.html', input_template_path='templates/report.html'):
    software_modules = load_modules_with_checks()
    # make sure sample_name has a value, if its nan, just put sample01 ... sampleN
    for idx, (key, value) in enumerate(merged_dict.items(), start=1):
        if not isinstance(value, dict):
            merged_dict[key] = {}
        if "sample_name" not in merged_dict[key] or pd.isna(merged_dict[key]["sample_name"]):
            merged_dict[key]["sample_name"] = f"sample{idx}"
    # convert the dictionary to a pandas dataframe
    df = pd.DataFrame.from_dict(merged_dict, orient="index")
    # plot the data
    # split columns into groups based on the column name before the first dot
    groups = df.columns.to_series().str.split(".").str[0]
    # seperate each group into a new dataframe
    unique_groups = groups.unique()
    unique_groups = unique_groups[unique_groups != "sample_name"]
    plotly_jinja_data = {'summary_table' : summary_table(df)}
    plotly_jinja_data['software_charts'] = ""
    for software in unique_groups:
        # Also include species column in the group
        group_df = df[[col for col in df.columns if col.startswith(software)]]
        # TODO: Species column is a protected column in this case. Need to make sure it doesn't exist prior.
        group_df = group_df.join(df[species].rename("species"))
        group_df.columns = group_df.columns.str.replace(f"{software}.", "", regex=False)
        if software in software_modules:
            plotly_jinja_data['software_charts'] += software_modules[software](group_df).plot()
        else:
            logging.warning("No plot module found for %s. Skipping plotting.", software)
        plotly_jinja_data['footer'] = make_footer()

    with open(output_html_path, "w", encoding="utf-8") as output_file:
        with open(input_template_path, encoding='utf-8') as template_file:
            j2_template = Template(template_file.read())
            output_file.write(j2_template.render(plotly_jinja_data))
    
def make_footer():
    import speccheck
    version = speccheck.__version__
    return f"<p>Produced with <a href=\"https://github.com/happykhan/speccheck\">speccheck</a> version {version}</p>"

            
def load_modules_with_checks():
    """Load Python modules with required checks from the 'plot_modules' directory."""
    module_dict = {}
    modules_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "plot_modules"
    )

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
