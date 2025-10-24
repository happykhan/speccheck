import os

import pytest

from speccheck.modules.speciator import Speciator


@pytest.fixture
def valid_tsv_file(tmp_path):
    file_content = (
        "Sample_id\ttaxId\tspeciesId\tspeciesName\tgenusId\tgenusName\tsuperkingdomId\tsuperkingdomName\treferenceId\tmashDistance\tpValue\tmatchingHashes\tconfidence\tsource\n"
        "1\t123\t456\tSpecies A\t789\tGenus A\t101112\tSuperkingdom A\t131415\t0.001\t0.05\t100\t0.95\tSource A\n"
    )
    file_path = tmp_path / "valid_file.tsv"
    file_path.write_text(file_content)
    return file_path


@pytest.fixture
def invalid_tsv_file(tmp_path):
    file_content = (
        "Sample_id,taxId,speciesId,speciesName,genusId,genusName,superkingdomId,superkingdomName,referenceId,mashDistance,pValue,matchingHashes,confidence,source\n"
        "1,123,456,Species A,789,Genus A,101112,Superkingdom A,131415,0.001,0.05,100,0.95,Source A\n"
        "1,123,456,Species A,789,Genus A,101112,Superkingdom A,131415,0.001,0.05,100,0.95,Source A\n"
    )
    file_path = tmp_path / "invalid_file.tsv"
    file_path.write_text(file_content)
    return file_path


def test_has_valid_fileformat_valid(valid_tsv_file):
    speciator = Speciator(valid_tsv_file)
    assert speciator.has_valid_fileformat


def test_has_valid_fileformat_invalid(invalid_tsv_file):
    speciator = Speciator(invalid_tsv_file)
    assert not speciator.has_valid_fileformat


def test_fetch_values_valid_file(valid_tsv_file):
    speciator = Speciator(valid_tsv_file)
    result = speciator.fetch_values()
    expected = {
        "Sample_id": 1,
        "taxId": 123,
        "speciesId": 456,
        "speciesName": "Species A",
        "genusId": 789,
        "genusName": "Genus A",
        "superkingdomId": 101112,
        "superkingdomName": "Superkingdom A",
        "referenceId": 131415,
        "mashDistance": 0.001,
        "pValue": 0.05,
        "matchingHashes": 100,
        "confidence": 0.95,
        "source": "Source A",
    }
    assert result == expected


def test_fetch_values_invalid_file(invalid_tsv_file):
    speciator = Speciator(invalid_tsv_file)
    with pytest.raises(ValueError, match="The file must contain exactly one row of values."):
        speciator.fetch_values()
