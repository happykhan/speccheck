import csv
import logging
import requests
from collections import defaultdict
from io import StringIO
from pathlib import Path

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
PREFERRED_SCHEMES = ["qualibact-v1.0", "enterobase-v2.3"]
CONTROLLED_FIELD_KEYS = {
    ("Checkm", "Completeness"),
    ("Checkm", "Contamination"),
    ("Checkm", "GC"),
    ("Checkm", "Genome size (bp)"),
    ("Checkm", "Marker lineage"),
    ("Checkm", "# contigs"),
    ("Checkm", "N50 (scaffolds)"),
    ("Quast", "GC (%)"),
    ("Quast", "Total length (>= 0 bp)"),
    ("Quast", "# contigs (>= 0 bp)"),
    ("Quast", "N50"),
    ("Speciator", "confidence"),
    ("Speciator", "genusName"),
    ("Speciator", "speciesName"),
    ("Sylph", "number_of_genomes"),
    ("Sylph", "species_name"),
}


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


def _choose_threshold_rows(rows):
    grouped = defaultdict(list)
    for row in rows:
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
        _make_row(
            species, "all", "Checkm", "Marker lineage", "regex", f"^{species}", "species_field"
        ),
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
        logging.warning(
            "Skipping unsupported QualiBact metric Total_Coding_Sequences for %s", species
        )
    else:
        logging.warning("Skipping unsupported QualiBact metric %s for %s", metric, species)
    return rows


def qualibact_rows_to_criteria_rows(rows):
    criteria_rows = []
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
        if key not in CONTROLLED_FIELD_KEYS:
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


def update_criteria_file(criteria_file, update_url=QUALIBACT_DEFAULT_URL):
    logging.info("Updating criteria file from %s", update_url)
    try:
        qualibact_rows = _fetch_qualibact_rows(update_url)
    except (requests.RequestException, ValueError) as exc:
        logging.error("Failed to download QualiBact thresholds: %s", exc)
        return

    generated_rows = qualibact_rows_to_criteria_rows(qualibact_rows)
    preserved_rows = _preserve_existing_rows(criteria_file)

    merged = []
    seen = set()
    for row in preserved_rows + generated_rows:
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

    logging.info("Criteria file updated successfully: %s", criteria_file)


if __name__ == "__main__":
    update_criteria_file("criteria.csv", QUALIBACT_DEFAULT_URL)
