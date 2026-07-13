from speccheck.modules.base import SingleRowTsvParser


class Speciator(SingleRowTsvParser):
    """Parse one Speciator taxonomic-assignment row."""

    software_name = "Speciator"
    description = "Speciator species assignment and confidence"
    supported_filenames = "TSV with the standard Speciator header"
    required_headers = (
        "Sample_id",
        "taxId",
        "speciesId",
        "speciesName",
        "genusId",
        "genusName",
        "superkingdomId",
        "superkingdomName",
        "referenceId",
        "mashDistance",
        "pValue",
        "matchingHashes",
        "confidence",
        "source",
    )
