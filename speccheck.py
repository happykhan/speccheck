#!/usr/bin/env python3
"""
This script processes reports by collecting and summarizing data from specified files.

Commands:
    collect: Collect and process QC data from files
    summary: Generate summary reports from collected data
    check: Validate criteria file integrity

Usage:
    python speccheck.py collect [OPTIONS] FILEPATHS...
    python speccheck.py summary [OPTIONS] DIRECTORY
    python speccheck.py check [OPTIONS]
"""

import logging
from typing import List, Optional
import typer
from rich.console import Console
from rich.logging import RichHandler
from speccheck.main import collect as collect_func, summary as summary_func, check as check_func
from speccheck import __version__


app = typer.Typer(help="Process QC reports for genomic data")
console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(console=console, show_time=True, show_level=True, show_path=False)
    ],
)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"speccheck version: {__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Process QC reports for genomic data.
    
    Use one of the subcommands: collect, summary, or check.
    """
    pass


@app.command()
def collect(
    filepaths: List[str] = typer.Argument(..., help="File paths with wildcards"),
    organism: Optional[str] = typer.Option(
        None,
        "--organism",
        help="Organism name. If not given, will be extracted from file paths.",
    ),
    sample: str = typer.Option(None, "--sample", help="Sample name"),
    criteria_file: str = typer.Option(
        "criteria.csv",
        "--criteria-file",
        help="File with criteria for processing",
    ),
    output_file: str = typer.Option(
        "qc_results/collected_data.csv",
        "--output-file",
        help="Output file for collected data",
    ),
    metadata: Optional[str] = typer.Option(
        None,
        "--metadata",
        help="CSV file with additional sample metadata (must have sample_id column)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Collect and process QC data from files."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    collect_func(organism, filepaths, criteria_file, output_file, sample, metadata)


@app.command()
def summary(
    directory: str = typer.Argument(..., help="Directory with reports"),
    output: str = typer.Option(
        "qc_report", "--output", help="Output folder for summary"
    ),
    species: str = typer.Option(
        "Speciator.speciesName", "--species", help="Field for species"
    ),
    sample: str = typer.Option("sample_id", "--sample", help="Field for sample name"),
    templates: str = typer.Option(
        "templates/report.html", "--templates", help="Template HTML file"
    ),
    plot: bool = typer.Option(False, "--plot", help="Enable plotting"),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Generate summary reports from collected data."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    summary_func(directory, output, species, sample, templates, plot)


@app.command()
def check(
    criteria_file: str = typer.Option(
        "criteria.csv",
        "--criteria-file",
        help="File with criteria for processing",
    ),
    update: bool = typer.Option(
        False, "--update", help="Update criteria with latest values"
    ),
    update_url: str = typer.Option(
        "https://raw.githubusercontent.com/happykhan/genomeqc/refs/heads/main/docs/summary/filtered_metrics.csv",
        "--update-url",
        help="URL to update criteria from",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Check criteria file integrity and optionally update it."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    check_func(criteria_file, update=update, update_url=update_url)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
