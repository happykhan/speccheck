import re
import csv


class Sylph:

    def __init__(self, file_path):
        self.file_path = file_path

    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):

        required_headers = [
            "Sample_file",
            "Genome_file",
            "Taxonomic_abundance",
            "Sequence_abundance",
            "Adjusted_ANI",
            "Eff_cov",
            "ANI_5-95_percentile",
            "Eff_lambda",
            "Lambda_5-95_percentile",
            "Median_cov",
            "Mean_cov_geq1",
            "Containment_ind",
            "Naive_ANI",
            "kmers_reassigned",
            "Contig_name",
        ]
        with open(self.file_path, "r", encoding="utf-8") as file:
            first_line = file.readline()
            if "\t" not in first_line:
                return False

        with open(self.file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
            lines = [line for line in lines if line.strip()]
        # Check if the first line is the header and has the required headers
        if first_line.strip().split("\t") != required_headers:
            return False

        return True

    def fetch_values(self):
        with open(self.file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter="\t")
            result = {
                "genomes": "",
                "number_of_genomes": 0,
                "taxonomic_abundances": "",
                "sequence_abundances": "",
                "adjusted_anis": "",
                "species_names": "",
                "top_species": "",
                "top_taxonomic_abundance": 0.0,
                "top_adjusted_ani": 0.0,
            }
            genomes = []
            species = []
            taxonomic_abundances = []
            sequence_abundances = []
            adjusted_anis = []

            for row in reader:
                # Skip lines that start with # (comments)
                if row.get("Sample_file", "").startswith("#"):
                    continue

                result["number_of_genomes"] += 1

                # Extract genome file name
                genome_file = row.get("Genome_file", "")
                genomes.append(genome_file)

                # Extract taxonomic and sequence abundances
                tax_abundance = float(row.get("Taxonomic_abundance", 0))
                seq_abundance = float(row.get("Sequence_abundance", 0))
                taxonomic_abundances.append(tax_abundance)
                sequence_abundances.append(seq_abundance)

                # Extract adjusted ANI
                adjusted_ani = float(row.get("Adjusted_ANI", 0))
                adjusted_anis.append(adjusted_ani)

                # Extract species name from Contig_name
                contig_name = row.get("Contig_name", "")
                match = re.search(r"(?<=\s)[A-Z][a-z]+ [a-z]+(?= strain)", contig_name)
                if match:
                    species_name = match.group(0)
                    species.append(species_name)
                else:
                    # Try alternative pattern for species extraction
                    alt_match = re.search(r"([A-Z][a-z]+ [a-z]+)", contig_name)
                    if alt_match:
                        species_name = alt_match.group(1)
                        species.append(species_name)
                    else:
                        species.append("Unknown")

            # Store all values as semicolon-separated strings
            result["genomes"] = ";".join(genomes)
            result["species_name"] = ";".join(species)
            result["taxonomic_abundances"] = ";".join(map(str, taxonomic_abundances))
            result["sequence_abundances"] = ";".join(map(str, sequence_abundances))
            result["adjusted_anis"] = ";".join(map(str, adjusted_anis))

            # Find top hit (highest taxonomic abundance)
            if taxonomic_abundances:
                max_abundance_idx = taxonomic_abundances.index(max(taxonomic_abundances))
                result["top_species"] = (
                    species[max_abundance_idx] if max_abundance_idx < len(species) else "Unknown"
                )
                result["top_taxonomic_abundance"] = taxonomic_abundances[max_abundance_idx]
                result["top_adjusted_ani"] = (
                    adjusted_anis[max_abundance_idx]
                    if max_abundance_idx < len(adjusted_anis)
                    else 0.0
                )

            return result
