import os
import importlib
import logging
import pandas as pd
from jinja2 import Template

def summary_table(df):
    # select sample_name column and all collumns ending with all_checks_passed
    sum_table = df[[col for col in df.columns if col.endswith("all_checks_passed")]]
    # Create a new column that is True if all checks passed
    sum_table["QC_PASS"] = sum_table.all(axis=1)
    # Change True/False to Pass / Fail
    sum_table = sum_table.replace({True: "Pass", False: "Fail"})
    # Rename columns to remove the all_checks_passed suffix
    sum_table.columns = sum_table.columns.str.replace(".all_checks_passed", "")
    return sum_table.to_html()


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

    with open(output_html_path, "w", encoding="utf-8") as output_file:
        with open(input_template_path, encoding='utf-8') as template_file:
            j2_template = Template(template_file.read())
            output_file.write(j2_template.render(plotly_jinja_data))

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
