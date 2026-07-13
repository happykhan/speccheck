from speccheck.modules.base import SingleRowTsvParser


class Checkm(SingleRowTsvParser):
    """Parse one CheckM2 quality-report row."""

    software_name = "Checkm"
    description = "CheckM2 completeness, contamination, and assembly metrics"
    supported_filenames = "TSV with the standard CheckM2 quality-report header"
    required_headers = (
        "Name",
        "Completeness",
        "Contamination",
        "Completeness_Model_Used",
        "Translation_Table_Used",
        "Coding_Density",
        "Contig_N50",
        "Average_Gene_Length",
        "Genome_Size",
        "GC_Content",
        "Total_Coding_Sequences",
        "Total_Contigs",
        "Max_Contig_Length",
        "Additional_Notes",
    )

    def fetch_values(self):
        parsed_row = super().fetch_values()

        gc_content = parsed_row.get("GC_Content")
        if isinstance(gc_content, (int, float)) and 0 <= gc_content <= 1:
            parsed_row["GC_Content"] = gc_content * 100

        return parsed_row
