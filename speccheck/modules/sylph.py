import re
import csv 

class Sylph():

    def __init__(self, file_path):
        self.file_path = file_path
    
    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):

        required_headers = [
            'Sample_file', 'Genome_file', 'Taxonomic_abundance', 'Sequence_abundance', 'Adjusted_ANI', 'Eff_cov', 'ANI_5-95_percentile', 'Eff_lambda', 'Lambda_5-95_percentile', 'Median_cov', 'Mean_cov_geq1', 'Containment_ind', 'Naive_ANI', 'kmers_reassigned', 'Contig_name'
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
            reader = csv.DictReader(file, delimiter='\t')
            result = {'genomes': '', 'number_of_genomes': 0}
            genomes = []
            for row in reader:
                genomes.append(row['Contig_name'].replace(',', ''))
                result['number_of_genomes'] += 1
            result['genomes'] = ';'.join(genomes)
        return result