from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PACKAGE_DIR.parent


def get_default_criteria_path():
    packaged_criteria = PACKAGE_DIR / "config" / "criteria.csv"
    if packaged_criteria.exists():
        return str(packaged_criteria)
    repo_criteria = REPO_ROOT / "criteria.csv"
    return str(repo_criteria)
