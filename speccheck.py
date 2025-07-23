#!/usr/bin/env python3
"""
This script processes reports by collecting and summarizing data from specified files.

Functions:
    main(): Entry point for the script. Parses command-line arguments and
    invokes the appropriate function.

Command-line Arguments:
    collect:
        -v, --verbose: Enable verbose output.
        organism: Organism name (str).
        filepaths: File paths with wildcards (list of str).
    summary:
        directory: Directory with reports (str).

Usage:
    python speccheck.py collect [-v] <organism> <filepaths>
    python speccheck.py summary <directory>
"""

import argparse
import logging
from rich.console import Console
from rich.logging import RichHandler
from speccheck.main import collect, summary, check
from speccheck import __version__


console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(console=console, show_time=True, show_level=True, show_path=False)
    ],
)


def main():
    """
    Main function to process reports.

    This function sets up an argument parser with two subcommands: 'collect' and 'summary'.
    - The 'collect' subcommand collects and processes files based on the provided
      organism name and file paths.
    - The 'summary' subcommand generates a summary from the specified directory containing reports.

    Arguments:
    - 'collect' subcommand:
        - -v, --verbose: Enable verbose output.
        - organism: Organism name (str).
        - filepaths: File paths with wildcards (list of str).
    - 'summary' subcommand:
        - directory: Directory with reports (str).

    If the 'verbose' flag is set, the logging level is set to DEBUG.

    The appropriate function is called based on the provided subcommand.
    """

    parser = argparse.ArgumentParser(description="Process reports")
    parser.add_argument(
        "--version", action="store_true", help="Prints version number", default=False
    )
    subparsers = parser.add_subparsers(dest="command")

    collect_parser = subparsers.add_parser("collect", help="Collect and process files")
    collect_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    collect_parser.add_argument(
        "--version", action="store_true", help="Prints version number", default=False
    )
    collect_parser.add_argument(
        "--organism",
        type=str,
        help="Organism name. If not given, the organism name will "
        + "be extracted from the file paths.",
    )
    collect_parser.add_argument("--sample", type=str, help="sample name")
    collect_parser.add_argument(
        "filepaths", type=str, nargs="+", help="File paths with wildcards"
    )
    collect_parser.add_argument(
        "--criteria-file",
        type=str,
        help="File with criteria for processing",
        default="criteria.csv",
    )
    collect_parser.add_argument(
        "--output-file",
        type=str,
        help="Output file for collected data",
        default="qc_results/collected_data.csv",
    )
    collect_parser.set_defaults(
        func=lambda args: collect(
            args.organism,
            args.filepaths,
            args.criteria_file,
            args.output_file,
            args.sample,
        )
    )

    summary_parser = subparsers.add_parser("summary", help="Generate summary")
    summary_parser.add_argument("directory", type=str, help="Directory with reports")
    summary_parser.add_argument(
        "--version", action="store_true", help="Prints version number", default=False
    )
    summary_parser.add_argument(
        "--output", type=str, help="Output folder for summary", default="qc_report"
    )
    summary_parser.add_argument(
        "--species", type=str, help="Field for species", default="Speciator.speciesName"
    )
    summary_parser.add_argument(
        "--sample", type=str, help="Field for samplename", default="Sample"
    )
    summary_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    summary_parser.add_argument(
        "--plot", action="store_true", help="Enable plotting", default=False
    )
    summary_parser.add_argument(
        "--templates",
        type=str,
        help="Template HTML file",
        default="templates/report.html",
    )
    summary_parser.set_defaults(
        func=lambda args: summary(
            args.directory,
            args.output,
            args.species,
            args.sample,
            args.templates,
            args.plot,
        )
    )
    check_parser = subparsers.add_parser("check", help="Check criteria file integrity")
    check_parser.add_argument(
        "--version", action="store_true", help="Prints version number", default=False
    )
    check_parser.add_argument(
        "--criteria-file",
        type=str,
        help="File with criteria for processing, default is criteria.csv",
        default="criteria.csv",
    )
    check_parser.add_argument(
        "--update",
        action="store_true",
        help="Update criteria with latest values",
        default=False,
    )
    check_parser.add_argument(
        "--update-url",
        type=str,
        help="URL to update criteria from",
        default="https://raw.githubusercontent.com/happykhan/genomeqc/refs/heads/main/docs/summary/filtered_metrics.csv",
    )
    check_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    check_parser.set_defaults(
        func=lambda args: check(
            args.criteria_file, update=args.update, update_url=args.update_url
        )
    )

    args = parser.parse_args()
    if args.version:
        console.print(__version__)
        return
    if hasattr(args, "func"):
        if args.version:
            console.print(__version__)
            return
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        args.func(args)
    else:
        logging.warning("No command specified. Try collect, summary or check\n")
        parser.print_help()


if __name__ == "__main__":
    main()
