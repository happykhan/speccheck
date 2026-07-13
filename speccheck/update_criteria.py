import csv
import logging
from collections import defaultdict
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import requests

QUALIBACT_DEFAULT_URL = "https://static.qualibact.org/api/v2/external/thresholds.csv"
CRITERIA_HEADERS = [
    "species",
    "assembly_type",
    "software",
    "field",
    "operator",
    "value",
    "special_field",
]
SNAPSHOT_HEADERS = [
    "species",
    "metric",
    "scheme",
    "source_url",
    "retrieved_at",
    "fallback_used",
    "FINAL_lower",
    "FINAL_upper",
    "WARN_lower",
    "WARN_upper",
]
PREFERRED_SCHEMES = ["qualibact-v1.1", "qualibact-v1.0"]
PACKAGE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = PACKAGE_DIR / "config"
QUALIBACT_SNAPSHOT_PATH = CONFIG_DIR / "qualibact_snapshot.csv"
QUALIBACT_SNAPSHOT_METADATA_PATH = CONFIG_DIR / "qualibact_snapshot_metadata.csv"
CONTROLLED_FIELD_KEYS = {
    ("Checkm", "Completeness"),
    ("Checkm", "Contamination"),
    ("Checkm", "GC"),
    ("Checkm", "Genome size (bp)"),
    ("Checkm", "# contigs"),
    ("Checkm", "N50 (scaffolds)"),
    ("Checkm", "Total_Coding_Sequences"),
    ("Quast", "GC (%)"),
    ("Quast", "Total length (>= 0 bp)"),
    ("Quast", "# contigs (>= 0 bp)"),
    ("Quast", "N50"),
    ("Speciator", "confidence"),
    ("Speciator", "genusName"),
    ("Speciator", "speciesName"),
    ("Sylph", "number_of_genomes"),
    ("Sylph", "species_name"),
    ("Sylph", "sequence_abundances"),
}
BASELINE_ROWS = (
    ("all", "all", "Sylph", "sequence_abundances", ">=", 99),
    ("all", "all", "Quast", "Total length (>= 0 bp)", ">=", 100000),
    ("all", "all", "Quast", "Total length (>= 0 bp)", "<=", 15000000),
    ("all", "all", "Checkm", "Genome size (bp)", ">=", 100000),
    ("all", "all", "Checkm", "Genome size (bp)", "<=", 15000000),
    ("all", "all", "Quast", "N50", ">=", 2000),
    ("all", "all", "Checkm", "N50 (scaffolds)", ">=", 2000),
    ("all", "short", "Quast", "# contigs (>= 0 bp)", "<=", 2000),
    ("all", "short", "Checkm", "# contigs", "<=", 2000),
    ("all", "all", "Checkm", "Contamination", "<=", 100),
)


def _normalize_number(value):
    if value in (None, ""):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    numeric = float(text)
    if numeric.is_integer():
        return int(numeric)
    return numeric


def _fetch_qualibact_rows(update_url):
    response = requests.get(update_url, timeout=30)
    response.raise_for_status()
    text = response.text.strip()
    if not text:
        raise ValueError("Received empty QualiBact response")
    return list(csv.DictReader(StringIO(text)))


def _scheme_priority(scheme):
    if scheme in PREFERRED_SCHEMES:
        return PREFERRED_SCHEMES.index(scheme)
    return len(PREFERRED_SCHEMES)


def _filter_supported_rows(rows):
    return [row for row in rows if row.get("scheme") in PREFERRED_SCHEMES]


def _choose_threshold_rows(rows):
    grouped = defaultdict(list)
    for row in _filter_supported_rows(rows):
        grouped[(row["species"], row["metric"])].append(row)

    chosen = []
    for group_rows in grouped.values():
        group_rows.sort(
            key=lambda row: (
                _scheme_priority(row.get("scheme", "")),
                row.get("source", ""),
            )
        )
        chosen.append(group_rows[0])
    return chosen


def _make_row(species, assembly_type, software, field, operator, value, special_field=""):
    return {
        "species": species,
        "assembly_type": assembly_type,
        "software": software,
        "field": field,
        "operator": operator,
        "value": value,
        "special_field": special_field,
    }


def _helper_rows_for_species(species):
    genus = species.split()[0]
    return [
        _make_row(species, "all", "Speciator", "confidence", "regex", "^good$"),
        _make_row(species, "all", "Speciator", "genusName", "regex", f"^{genus}"),
        _make_row(
            species, "all", "Speciator", "speciesName", "regex", f"^{species}", "species_field"
        ),
        _make_row(species, "all", "Sylph", "number_of_genomes", "=", 1),
        _make_row(species, "all", "Sylph", "species_name", "regex", f"^{species}", "species_field"),
    ]


def _rows_from_threshold(species, metric, lower, upper):
    rows = []

    def add_bounds(assembly_type, software, field):
        if lower is not None:
            rows.append(_make_row(species, assembly_type, software, field, ">=", lower))
        if upper is not None:
            rows.append(_make_row(species, assembly_type, software, field, "<=", upper))

    if metric == "Genome_Size":
        add_bounds("all", "Checkm", "Genome size (bp)")
        add_bounds("all", "Quast", "Total length (>= 0 bp)")
    elif metric == "GC_Content":
        add_bounds("all", "Checkm", "GC")
        add_bounds("all", "Quast", "GC (%)")
    elif metric == "no_of_contigs":
        add_bounds("short", "Checkm", "# contigs")
        add_bounds("short", "Quast", "# contigs (>= 0 bp)")
    elif metric == "N50":
        add_bounds("short", "Checkm", "N50 (scaffolds)")
        add_bounds("short", "Quast", "N50")
    elif metric == "Completeness":
        add_bounds("all", "Checkm", "Completeness")
    elif metric == "Contamination":
        add_bounds("all", "Checkm", "Contamination")
    elif metric == "Total_Coding_Sequences":
        add_bounds("all", "Checkm", "Total_Coding_Sequences")
    else:
        logging.warning("Skipping unsupported QualiBact metric %s for %s", metric, species)
    return rows


def _baseline_criteria_rows():
    return [
        _make_row(species, assembly_type, software, field, operator, value)
        for species, assembly_type, software, field, operator, value in BASELINE_ROWS
    ]


def qualibact_rows_to_criteria_rows(rows):
    criteria_rows = _baseline_criteria_rows()
    seen_species = set()
    for row in _choose_threshold_rows(rows):
        species = row["species"].replace("_", " ")
        metric = row["metric"]
        lower = _normalize_number(row.get("FINAL_lower"))
        upper = _normalize_number(row.get("FINAL_upper"))
        if species not in seen_species:
            criteria_rows.extend(_helper_rows_for_species(species))
            seen_species.add(species)
        criteria_rows.extend(_rows_from_threshold(species, metric, lower, upper))
    return criteria_rows


def _preserve_existing_rows(criteria_file):
    path = Path(criteria_file)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as handle:
        existing_rows = list(csv.DictReader(handle))
    preserved = []
    for row in existing_rows:
        key = (row.get("software"), row.get("field"))
        if key not in CONTROLLED_FIELD_KEYS and row.get("species") != "all":
            preserved.append(
                {
                    "species": row.get("species", ""),
                    "assembly_type": row.get("assembly_type", ""),
                    "software": row.get("software", ""),
                    "field": row.get("field", ""),
                    "operator": row.get("operator", ""),
                    "value": row.get("value", ""),
                    "special_field": row.get("special_field", ""),
                }
            )
    return preserved


def _write_snapshot_artifacts(rows, update_url, snapshot_dir=CONFIG_DIR):
    snapshot_dir = Path(snapshot_dir)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = snapshot_dir / QUALIBACT_SNAPSHOT_PATH.name
    metadata_path = snapshot_dir / QUALIBACT_SNAPSHOT_METADATA_PATH.name
    chosen_rows = _choose_threshold_rows(rows)
    retrieved_at = datetime.now(timezone.utc).isoformat()
    snapshot_rows = []
    metadata_rows = {}
    for row in chosen_rows:
        species = row["species"].replace("_", " ")
        scheme = row.get("scheme", "")
        fallback_used = scheme != PREFERRED_SCHEMES[0]
        snapshot_rows.append(
            {
                "species": species,
                "metric": row.get("metric", ""),
                "scheme": scheme,
                "source_url": update_url,
                "retrieved_at": retrieved_at,
                "fallback_used": str(fallback_used),
                "FINAL_lower": row.get("FINAL_lower", ""),
                "FINAL_upper": row.get("FINAL_upper", ""),
                "WARN_lower": row.get("WARN_lower", ""),
                "WARN_upper": row.get("WARN_upper", ""),
            }
        )
        metadata_rows[species] = {
            "species": species,
            "scheme": scheme,
            "threshold_source": f"QualiBact {species} {scheme}",
            "source_url": update_url,
            "retrieved_at": retrieved_at,
            "fallback_used": str(fallback_used),
        }

    with open(snapshot_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SNAPSHOT_HEADERS)
        writer.writeheader()
        writer.writerows(sorted(snapshot_rows, key=lambda row: (row["species"], row["metric"])))

    with open(metadata_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "species",
                "scheme",
                "threshold_source",
                "source_url",
                "retrieved_at",
                "fallback_used",
            ],
        )
        writer.writeheader()
        writer.writerows(sorted(metadata_rows.values(), key=lambda row: row["species"]))


def get_threshold_source_for_species(species):
    if QUALIBACT_SNAPSHOT_METADATA_PATH.exists():
        with open(QUALIBACT_SNAPSHOT_METADATA_PATH, encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("species") == species:
                    return {
                        "threshold_source": row.get("threshold_source", ""),
                        "scheme": row.get("scheme", ""),
                        "fallback_used": row.get("fallback_used", "False"),
                    }
    criteria_path = CONFIG_DIR / "criteria.csv"
    if criteria_path.exists():
        with open(criteria_path, encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("species") == species:
                    return {
                        "threshold_source": "Packaged QualiBact species thresholds",
                        "scheme": "packaged",
                        "fallback_used": "False",
                    }
    return {
        "threshold_source": "Global baseline only",
        "scheme": "",
        "fallback_used": "False",
    }


def update_criteria_file(
    criteria_file,
    update_url=QUALIBACT_DEFAULT_URL,
    *,
    snapshot_dir=CONFIG_DIR,
):
    logging.info("Updating criteria file from %s", update_url)
    try:
        qualibact_rows = _fetch_qualibact_rows(update_url)
    except (requests.RequestException, ValueError) as exc:
        logging.error("Failed to download QualiBact thresholds: %s", exc)
        return False

    if not _choose_threshold_rows(qualibact_rows):
        logging.warning(
            "No supported QualiBact rows found at %s after excluding non-QualiBact schemes. "
            "Keeping existing species-specific thresholds.",
            update_url,
        )
        return False

    generated_rows = qualibact_rows_to_criteria_rows(qualibact_rows)
    preserved_rows = _preserve_existing_rows(criteria_file)

    merged = []
    seen = set()
    for row in generated_rows + preserved_rows:
        normalized = {header: row.get(header, "") for header in CRITERIA_HEADERS}
        row_key = tuple(normalized[header] for header in CRITERIA_HEADERS)
        if row_key in seen:
            continue
        seen.add(row_key)
        merged.append(normalized)

    merged.sort(
        key=lambda row: (
            row["species"],
            row["assembly_type"],
            row["software"],
            row["field"],
            row["operator"],
        )
    )

    with open(criteria_file, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CRITERIA_HEADERS)
        writer.writeheader()
        writer.writerows(merged)

    _write_snapshot_artifacts(qualibact_rows, update_url, snapshot_dir=snapshot_dir)
    logging.info("Criteria file updated successfully: %s", criteria_file)
    return True


if __name__ == "__main__":
    update_criteria_file("criteria.csv", QUALIBACT_DEFAULT_URL)
