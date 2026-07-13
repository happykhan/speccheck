from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent


def get_default_criteria_path():
    packaged_criteria = PACKAGE_DIR / "config" / "criteria.csv"
    return str(packaged_criteria)
