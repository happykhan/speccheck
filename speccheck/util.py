"""
Load Python modules with required checks from the 'modules' directory.
This function scans the 'modules' directory for Python files, loads each file as a module,
and checks if the module contains a class with the same name as the file in TitleCase.
If the class has a method named 'has_valid_fileformat', it is added to the list of loaded modules.
    list of type: List of loaded classes that have the 'has_valid_fileformat' method.
"""

import glob
import importlib.util
import logging
import os


def get_all_files(filepaths):
    """
    Given a list of file paths, return a list of absolute paths to all files.

    This function takes a list of file paths and checks if each path is a directory.
    If it is a directory, it appends a wildcard to the path to match all files in the directory.
    It then uses the glob module to find all files matching the path pattern and adds their
    absolute paths to the result list. If no files match the pattern, a warning is logged.

    Args:
        filepaths (list of str): List of file paths or directory paths.

    Returns:
        list of str: List of absolute paths to all matched files.
    """

    all_paths = []
    for path in filepaths:
        if os.path.isdir(path):
            path = os.path.join(path, "*")
        files = glob.glob(path, recursive=False)
        if not files:
            logging.warning("No files matched the given pattern: %s", path)
        else:
            for file in files:
                all_paths.append(os.path.abspath(file))
    return all_paths


def load_modules_with_checks():
    """Load Python modules with required checks from the 'modules' directory."""
    module_list = []
    modules_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules")

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

        # Check if module has a class matching its name in TitleCase
        class_name = module_name.title()
        if hasattr(module, class_name):
            cla = getattr(module, class_name)
            if hasattr(cla, "has_valid_fileformat"):
                module_list.append(cla)

    loaded_classes = ", ".join([cls.__name__ for cls in module_list])
    logging.debug("Loaded modules: %s", loaded_classes)
    return module_list
