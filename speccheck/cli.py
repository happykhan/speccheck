#!/usr/bin/env python3
"""
This script processes reports by collecting and summarizing data from specified files.

Commands:
    collect: Collect and process QC data from files
    summary: Generate summary reports from collected data
    check: Validate criteria file integrity

Usage:
    speccheck collect [OPTIONS] FILEPATHS...
    speccheck summary [OPTIONS] DIRECTORY
    speccheck check [OPTIONS]
"""

import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from speccheck import __version__
from speccheck.config import get_default_criteria_path
from speccheck.main import check as check_func
from speccheck.main import collect as collect_func
from speccheck.main import collect_ghru as collect_ghru_func
from speccheck.main import summary as summary_func
from speccheck.registry import get_parser_classes
from speccheck.report import get_default_template_path
from speccheck.update_criteria import QUALIBACT_DEFAULT_URL
from speccheck.util import get_all_files

app = typer.Typer(help="Process QC reports for genomic data")
console = Console()


def configure_logging(*, verbose=False, quiet=False, log_file=None):
    """Configure concise terminal logs and an optional plain-text audit log."""
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    handlers = [RichHandler(console=console, show_time=True, show_level=True, show_path=False)]
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=handlers,
        force=True,
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
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show diagnostic details"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Only show warnings and errors"),
    log_file: str | None = typer.Option(
        None, "--log-file", help="Also write a timestamped plain-text run log"
    ),
):
    """
    Process QC reports for genomic data.

    Use one of the subcommands: collect, summary, or check.
    """
    if verbose and quiet:
        raise typer.BadParameter("--verbose and --quiet cannot be used together")
    configure_logging(verbose=verbose, quiet=quiet, log_file=log_file)


@app.command()
def collect(
    filepaths: list[str] = typer.Argument(..., help="File paths with wildcards"),
    organism: str | None = typer.Option(
        None,
        "--organism",
        help="Organism name. If not given, will be extracted from file paths.",
    ),
    sample: str = typer.Option(None, "--sample", help="Sample name"),
    criteria_file: str = typer.Option(
        get_default_criteria_path(),
        "--criteria-file",
        help="File with criteria for processing",
    ),
    output_file: str = typer.Option(
        "qc_results/collected_data.csv",
        "--output-file",
        help="Output file for collected data",
    ),
    metadata: str | None = typer.Option(
        None,
        "--metadata",
        help="CSV file with additional sample metadata (must have sample_id column)",
    ),
    assembly_type: str = typer.Option(
        "short",
        "--assembly-type",
        help="Criteria assembly mode: all, short, long, or hybrid",
    ),
    allow_unknown_organism: bool = typer.Option(
        False,
        "--allow-unknown-organism",
        help="Allow fallback criteria when organism cannot be inferred from parser outputs",
    ),
    fail_on_not_evaluated: bool = typer.Option(
        False,
        "--fail-on-not-evaluated/--no-fail-on-not-evaluated",
        help="Treat missing expected metrics as failed parser/sample checks",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
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

    collect_func(
        organism,
        filepaths,
        criteria_file,
        output_file,
        sample,
        metadata,
        allow_unknown_organism=allow_unknown_organism,
        assembly_type=assembly_type,
        fail_on_not_evaluated=fail_on_not_evaluated,
    )


@app.command()
def summary(
    directory: str = typer.Argument(..., help="Directory with reports"),
    output: str = typer.Option("qc_report", "--output", help="Output folder for summary"),
    species: str = typer.Option("Speciator.speciesName", "--species", help="Field for species"),
    sample: str = typer.Option("sample_id", "--sample", help="Field for sample name"),
    templates: str = typer.Option(
        get_default_template_path(), "--templates", help="Template HTML file"
    ),
    plot: bool = typer.Option(False, "--plot", help="Enable plotting"),
    xlsx_output: str | None = typer.Option(
        None,
        "--xlsx-output",
        help="Optional XLSX workbook path for merged summary output",
    ),
    interactive_tables: bool = typer.Option(
        True,
        "--interactive-tables/--no-interactive-tables",
        help="Enable sortable and filterable report tables",
    ),
    qualifyr_style: bool = typer.Option(
        False,
        "--qualifyr-style/--no-qualifyr-style",
        help="Render compact built-in summary tables in a qualifyr-like layout",
    ),
    qualibact_compat: bool = typer.Option(
        False,
        "--qualibact-compat/--no-qualibact-compat",
        help="Add pinned QualiBact E. coli v1 PASS/WARN/FAIL compatibility columns",
    ),
    qualibact_warn_as_fail: bool = typer.Option(
        False,
        "--qualibact-warn-as-fail",
        help="Treat QualiBact WARN tier as failing in all_checks_passed when compatibility mode is enabled",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
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

    summary_func(
        directory,
        output,
        species,
        sample,
        templates,
        plot,
        xlsx_output=xlsx_output,
        interactive_tables=interactive_tables,
        qualifyr_style=qualifyr_style,
        qualibact_compat=qualibact_compat,
        qualibact_warn_as_fail=qualibact_warn_as_fail,
    )


@app.command("collect-ghru")
def collect_ghru(
    ghru_output_dir: str = typer.Argument(..., help="GHRU output directory"),
    output_dir: str = typer.Argument(..., help="Directory for per-sample collected CSVs"),
    sample: list[str] | None = typer.Option(
        None,
        "--sample",
        help="Optional sample name(s) to restrict collection",
    ),
    organism: str | None = typer.Option(
        None,
        "--organism",
        help="Optional organism override for all selected samples",
    ),
    criteria_file: str = typer.Option(
        get_default_criteria_path(),
        "--criteria-file",
        help="File with criteria for processing",
    ),
    metadata: str | None = typer.Option(
        None,
        "--metadata",
        help="CSV file with additional sample metadata (must have sample_id column)",
    ),
    work_dir: str | None = typer.Option(
        None,
        "--work-dir",
        help="Optional Nextflow work directory to search for unpublished depth files",
    ),
    allow_unknown_organism: bool = typer.Option(
        False,
        "--allow-unknown-organism",
        help="Allow fallback criteria when organism cannot be inferred from parser outputs",
    ),
    fail_on_not_evaluated: bool = typer.Option(
        False,
        "--fail-on-not-evaluated/--no-fail-on-not-evaluated",
        help="Treat missing expected metrics as failed parser/sample checks",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """Collect per-sample QC CSVs directly from a GHRU output tree."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    collect_ghru_func(
        ghru_output_dir,
        output_dir,
        criteria_file,
        organism=organism,
        metadata_file=metadata,
        allow_unknown_organism=allow_unknown_organism,
        fail_on_not_evaluated=fail_on_not_evaluated,
        work_dir=work_dir,
        sample_ids=sample,
    )


@app.command()
def check(
    criteria_file: str = typer.Option(
        get_default_criteria_path(),
        "--criteria-file",
        help="File with criteria for processing",
    ),
    update: bool = typer.Option(False, "--update", help="Update criteria with latest values"),
    update_url: str = typer.Option(
        QUALIBACT_DEFAULT_URL,
        "--update-url",
        help="URL to update criteria from",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
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


@app.command("modules")
def modules_command():
    """List input formats available in this installation."""
    table = Table(title="Supported input modules")
    table.add_column("Software", style="cyan", no_wrap=True)
    table.add_column("Accepted input")
    table.add_column("Purpose")
    for parser in get_parser_classes():
        table.add_row(
            parser.software_name or parser.__name__,
            parser.supported_filenames or "See parser documentation",
            parser.description or "QC metric parser",
        )
    console.print(table)


@app.command("inspect")
def inspect_inputs(
    filepaths: list[str] = typer.Argument(..., help="Files or directories to inspect"),
):
    """Identify which files Speccheck recognises without writing output."""
    table = Table(title="Input inspection")
    table.add_column("File")
    table.add_column("Detected module", style="cyan")
    recognised = 0
    for file_path in get_all_files(filepaths):
        detected = []
        for parser_class in get_parser_classes():
            parser = parser_class(file_path)
            if parser.has_valid_filename and parser.has_valid_fileformat:
                detected.append(parser.software_name or parser.__class__.__name__)
        if detected:
            recognised += 1
        table.add_row(file_path, ", ".join(detected) or "not recognised")
    console.print(table)
    console.print(f"Recognised {recognised} input file(s).")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
