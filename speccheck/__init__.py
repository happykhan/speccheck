
"""
SpecCheck: A bioinformatics software focused on quality control based on species criteria

This package provides tools for quality control in bioinformatics data
with a focus on species-specific criteria.

Author: Nabil-Fareed Alikhan (nabil@happykhan.com)
License: GPLv3
Version: 1.1.1
"""
__version__ = "1.1.1"
__author__ = "Nabil-Fareed Alikhan"
__email__ = "nabil@happykhan.com"
__license__ = "GPLv3"
__description__ = "A bioinformatics software focused on quality control based on species criteria"
__module_name__ = "speccheck"
__url__ = "https://github.com/happykhan/speccheck"

# Import main entry point for CLI
from speccheck.cli import main

__all__ = ['main', '__version__', '__author__', '__email__', '__license__', '__description__', '__module_name__', '__url__']
