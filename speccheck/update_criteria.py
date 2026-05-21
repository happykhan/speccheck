"""
Update speccheck criteria.csv with thresholds from the QualiBact v2 API.

Fetches published thresholds from https://static.qualibact.org/api/v2/thresholds.csv,
maps QualiBact metrics to speccheck criteria fields, and updates the values in-place.

Usage:
    python -m speccheck.update_criteria [criteria_file] [--url URL] [--scheme SCHEME]
"""

import argparse
import csv
import io
import logging
import sys

import requests

logger = logging.getLogger(__name__)

DEFAULT_URL = "https://static.qualibact.org/api/v2/thresholds.csv"
DEFAULT_SCHEME = "qualibact-v1.1"
DEFAULT_CRITERIA_FILE = "criteria.csv"

# Maps QualiBact metric names to (software, field) pairs used in criteria.csv.
# Each metric may appear in multiple software columns (e.g. Checkm and Quast both
# track GC and genome size).
METRIC_MAP: dict[str, list[tuple[str, str]]] = {
    "Genome_Size": [
        ("Checkm", "Genome size (bp)"),
        ("Quast", "Total length (>= 0 bp)"),
    ],
    "GC_Content": [
        ("Checkm", "GC"),
        ("Quast", "GC (%)"),
    ],
    "Completeness_Specific": [
        ("Checkm", "Completeness"),
    ],
    "Contamination": [
        ("Checkm", "Contamination"),
    ],
    "N50": [
        ("Checkm", "N50 (scaffolds)"),
        ("Quast", "N50"),
    ],
    "no_of_contigs": [
        ("Checkm", "# contigs"),
        ("Quast", "# contigs (>= 0 bp)"),
    ],
    "Total_Coding_Sequences": [],  # No matching criteria.csv field currently
}


def fetch_qualibact_thresholds(
    url: str, scheme: str
) -> dict[str, dict[str, tuple[str, str]]]:
    """
    Fetch QualiBact thresholds CSV and return parsed data.

    Returns a nested dict:
        {species: {metric: (FINAL_lower, FINAL_upper)}}

    Only rows matching the requested scheme are included.
    """
    logger.info("Fetching QualiBact thresholds from %s (scheme=%s)", url, scheme)
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        raise ValueError("Received empty response from QualiBact API")

    reader = csv.DictReader(io.StringIO(response.text))
    thresholds: dict[str, dict[str, tuple[str, str]]] = {}

    for row in reader:
        if row.get("scheme") != scheme:
            continue
        species = row.get("species", "").strip()
        metric = row.get("metric", "").strip()
        if not species or not metric:
            continue
        lower = row.get("FINAL_lower", "").strip()
        upper = row.get("FINAL_upper", "").strip()
        thresholds.setdefault(species, {})[metric] = (lower, upper)

    logger.info(
        "Loaded thresholds for %d species and up to %d metrics",
        len(thresholds),
        len({m for sp in thresholds.values() for m in sp}),
    )
    return thresholds


def _format_value(value: str) -> str:
    """
    Format a numeric value string for criteria.csv.

    Strips trailing '.0' from values that are effectively integers,
    so we get '97' instead of '97.0'.
    """
    try:
        num = float(value)
        if num == int(num) and "e" not in value.lower():
            return str(int(num))
        return value
    except (ValueError, OverflowError):
        return value


def update_criteria(
    criteria_rows: list[dict[str, str]],
    thresholds: dict[str, dict[str, tuple[str, str]]],
) -> list[dict[str, str]]:
    """
    Apply QualiBact thresholds to criteria rows in-place and return the updated list.

    Rules:
    - Only rows where assembly_type != 'long' are updated
    - FINAL_lower updates rows with operator '>='
    - FINAL_upper updates rows with operator '<='
    - Empty/missing bounds are skipped
    """
    criteria_species = {
        row["species"] for row in criteria_rows if row["species"] != "all"
    }
    api_species = set(thresholds.keys())

    # Warn about species mismatches
    only_in_api = api_species - criteria_species
    only_in_criteria = criteria_species - api_species

    if only_in_api:
        logger.warning(
            "Species in QualiBact API but not in criteria.csv: %s",
            ", ".join(sorted(only_in_api)),
        )
    if only_in_criteria:
        logger.warning(
            "Species in criteria.csv but not in QualiBact API: %s",
            ", ".join(sorted(only_in_criteria)),
        )

    # Track which metrics could not be mapped
    unmapped_metrics: set[str] = set()
    updated_count = 0

    for species, metrics in thresholds.items():
        for metric_name, (lower, upper) in metrics.items():
            targets = METRIC_MAP.get(metric_name)
            if targets is None:
                unmapped_metrics.add(metric_name)
                continue
            if not targets:
                # Metric is known but has no criteria.csv mapping (e.g. Total_Coding_Sequences)
                continue

            for software, field in targets:
                for row in criteria_rows:
                    if row["species"] != species:
                        continue
                    if row["assembly_type"] == "long":
                        continue
                    if row["software"] != software or row["field"] != field:
                        continue

                    if lower and row["operator"] == ">=":
                        old_val = row["value"]
                        row["value"] = _format_value(lower)
                        if old_val != row["value"]:
                            logger.debug(
                                "Updated %s / %s %s >= : %s -> %s",
                                species, software, field, old_val, row["value"],
                            )
                            updated_count += 1

                    if upper and row["operator"] == "<=":
                        old_val = row["value"]
                        row["value"] = _format_value(upper)
                        if old_val != row["value"]:
                            logger.debug(
                                "Updated %s / %s %s <= : %s -> %s",
                                species, software, field, old_val, row["value"],
                            )
                            updated_count += 1

    if unmapped_metrics:
        logger.warning(
            "QualiBact metrics with no criteria.csv mapping: %s",
            ", ".join(sorted(unmapped_metrics)),
        )

    logger.info("Updated %d values in criteria.csv", updated_count)
    return criteria_rows


def read_criteria(criteria_file: str) -> list[dict[str, str]]:
    """Read criteria.csv and return rows as list of dicts."""
    with open(criteria_file, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_criteria(criteria_file: str, rows: list[dict[str, str]]) -> None:
    """Write criteria rows back to CSV, preserving column order."""
    fieldnames = [
        "species",
        "assembly_type",
        "software",
        "field",
        "operator",
        "value",
        "special_field",
    ]
    with open(criteria_file, "w", encoding="utf-8", newline="\n") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def update_criteria_file(
    criteria_file: str = DEFAULT_CRITERIA_FILE,
    url: str = DEFAULT_URL,
    scheme: str = DEFAULT_SCHEME,
) -> None:
    """
    Main entry point: fetch QualiBact thresholds and update the criteria file.
    """
    logger.info("Updating %s from QualiBact API (%s, scheme=%s)", criteria_file, url, scheme)

    thresholds = fetch_qualibact_thresholds(url, scheme)
    if not thresholds:
        logger.error("No thresholds found for scheme '%s'. Aborting.", scheme)
        return

    rows = read_criteria(criteria_file)
    update_criteria(rows, thresholds)
    write_criteria(criteria_file, rows)
    logger.info("Criteria file updated successfully: %s", criteria_file)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Update speccheck criteria.csv from QualiBact v2 API thresholds."
    )
    parser.add_argument(
        "criteria_file",
        nargs="?",
        default=DEFAULT_CRITERIA_FILE,
        help="Path to the criteria CSV file (default: %(default)s)",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help="URL for the QualiBact thresholds CSV (default: %(default)s)",
    )
    parser.add_argument(
        "--scheme",
        default=DEFAULT_SCHEME,
        help="QualiBact scheme to use (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        update_criteria_file(args.criteria_file, args.url, args.scheme)
    except requests.RequestException as e:
        logger.error("Failed to fetch QualiBact thresholds: %s", e)
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to update criteria: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
