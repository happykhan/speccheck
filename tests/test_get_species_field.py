import csv
import os

import pytest

from speccheck.criteria import get_species_field


def test_get_species_field_valid():
    # Arrange
    criteria_file = "test_criteria_valid.csv"
    with open(criteria_file, "w", encoding="utf-8") as f:
        f.write("species,assembly_type,software,field,operator,value,special_field\n")
        f.write("all,all,Speciator,speciesName,regex,^.+,species_field\n")
        f.write("all,all,CheckM,Marker lineage,regex,^.+,species_field\n")
        f.write("all,all,CheckM,GC,<=,70,\n")

    expected_output = [
        {"software": "Speciator", "field": "speciesName"},
        {"software": "CheckM", "field": "Marker lineage"},
    ]

    # Act
    result = get_species_field(criteria_file)
    # delete test file
    os.remove(criteria_file)
    # Assert
    assert result == expected_output


def test_get_species_field_no_species_field():
    # Arrange
    criteria_file = "test_criteria_no_species_field.csv"
    with open(criteria_file, "w", encoding="utf-8") as f:
        f.write("species,assembly_type,software,field,operator,value,special_field\n")
        f.write("all,short,CheckM,N50 (scaffolds),>,15000,\n")

    expected_output = []

    # Act
    result = get_species_field(criteria_file)
    os.remove(criteria_file)
    # Assert
    assert result == expected_output


def test_get_species_field_but_numeric():
    # Arrange
    criteria_file = "test_criteria_no_species_field.csv"
    with open(criteria_file, "w", encoding="utf-8") as f:
        f.write("species,assembly_type,software,field,operator,value,special_field\n")
        f.write("all,short,CheckM,N50 (scaffolds),>,15000,species_field\n")

    expected_output = []

    # Act
    result = get_species_field(criteria_file)
    os.remove(criteria_file)
    # Assert
    assert result == expected_output
