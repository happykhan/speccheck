import tomllib

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

try:
    __version__ = version("speccheck-qc")
except PackageNotFoundError:  # pragma: no cover - fallback for source-only execution
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "rb") as handle:
            __version__ = tomllib.load(handle)["project"]["version"]
    else:
        __version__ = "0+unknown"

__author__ = "Nabil-Fareed Alikhan"
__email__ = "nabil@happykhan.com"
__license__ = "GPLv3"
__description__ = "A bioinformatics software focused on quality control based on species criteria"
__module_name__ = "speccheck"
__url__ = "https://github.com/happykhan/speccheck"

from speccheck.cli import main

__all__ = [
    "main",
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
    "__module_name__",
    "__url__",
]
