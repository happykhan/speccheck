import logging
import requests
import csv

METRICS = {
    "N50": ["N50", "N50 (scaffolds)", "N50 (contigs)"],
    "GC_Content": ["GC", "GC_Content", "GC (%)"],
    "no_of_contigs": [
        "no_of_contigs",
        "Contig_Count",
        "# contigs (>= 0 bp)",
        "# contigs",
    ],
    "Genome_Size": ["Genome_Size", "Total length (>= 0 bp)"],
    "Completeness": ["Completeness"],
    "Contamination": ["Contamination"],
    "Total_Coding_Sequences": ["Total_Coding_Sequences"],
}


def update_criteria_file(criteria_file, update_url):
    """
    Update the criteria file with the latest values from the given URL.
    """
    logging.info("Updating criteria file from %s", update_url)
    with open(criteria_file, "r", encoding="utf-8") as f:
        current_criteria = list(csv.DictReader(f))

    try:
        response = requests.get(update_url, timeout=10)
        response.raise_for_status()
        # make response a dictionary
        # Convert csv into list of dictionaries
        if not response.text.strip():
            logging.error("Received empty response from the update URL.")
            return
        csv_lines = response.text.strip().split("\n")
        headers = csv_lines[0].split(",")
        updated_criteria = [dict(zip(headers, line.split(","))) for line in csv_lines[1:]]
        # Change species by replacing _ with a space
        for row in updated_criteria:
            if "species" in row:
                row["species"] = row["species"].replace("_", " ")
        # Get current criteria file
        current_criteria_list = [row for row in current_criteria]
        # Check if species are missing.
        species_not_in_update_list = set(
            current_species := {row["species"] for row in current_criteria_list if "species" in row}
        ) - set(updated_species := {row["species"] for row in updated_criteria if "species" in row})
        # Remove "all" from species not in update list
        species_not_in_update_list.discard("all")
        if species_not_in_update_list:
            logging.warning(
                "Species %s not found in the online criteria.",
                ", ".join(species_not_in_update_list),
            )
        # Speces not in the current list
        species_not_in_current_list = set(updated_species) - set(current_species)
        if species_not_in_current_list:
            logging.warning(
                "Species %s found in the online criteria but not in the current criteria file.",
                ", ".join(species_not_in_current_list),
            )
        for row in updated_criteria:
            # find rows in current_criteria where 'species' is the same, assembly_type is not long, and other conditions
            matching_rows = [
                r
                for r in current_criteria_list
                if r.get("species") == row.get("species")
                and r.get("assembly_type") != "long"
                and r.get("field") in METRICS.get(row.get("metric", ""), [])
            ]
            for m_row in matching_rows:
                if row.get("lower_bounds") and m_row.get("operator") == ">=":
                    # if the value ends with .0 or .00, remove it)
                    m_row["value"] = row["lower_bounds"]
                    logging.debug(
                        "Setting lower bounds for %s to %s",
                        row.get("field"),
                        m_row["value"],
                    )
                if row.get("upper_bounds") and m_row.get("operator") == "<=":
                    m_row["value"] = row["upper_bounds"]
                    logging.debug(
                        "Setting upper bounds for %s to %s",
                        row.get("field"),
                        m_row["value"],
                    )
        # Fix some minor stuff.
        for row in current_criteria_list:
            if row["field"] in METRICS.get("no_of_contigs", []) and row["operator"] == ">=":
                # Delete this row
                current_criteria_list.remove(row)
            # Acinetobacter baumannii,all,Sylph,species_name,regex,^,species_field
            # Set to species
            if (
                row["software"] == "Sylph"
                and row["field"] == "species_name"
                and row["operator"] == "regex"
                and row["value"] == "^"
            ):
                row["value"] = f"^{row['species']}"
                logging.debug("Changing field from species_name to species for Sylph")
        with open(criteria_file, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=current_criteria_list[0].keys())
            writer.writeheader()
            writer.writerows(current_criteria_list)

        logging.info("Criteria file updated successfully: %s", criteria_file)
    except requests.RequestException as e:
        logging.error("Failed to update criteria file: %s", e)


if __name__ == "__main__":
    update_criteria_file(
        "criteria.csv",
        "https://raw.githubusercontent.com/happykhan/genomeqc/refs/heads/main/docs/summary/filtered_metrics.csv",
    )
