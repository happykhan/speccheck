import re
import csv 

class Checkm():

    def __init__(self, file_path):
        self.file_path = file_path

    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):

        required_headers = [
            'Name',
            'Completeness',
            'Contamination',
            'Completeness_Model_Used',
            'Translation_Table_Used',
            'Coding_Density',
            'Contig_N50',
            'Average_Gene_Length',
            'Genome_Size',
            'GC_Content',
            'Total_Coding_Sequences',
            'Total_Contigs',
            'Max_Contig_Length',
            'Additional_Notes'
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
            row_count = 0
            for row in reader:
                parsed_row = {}
                row_count += 1
                for key, value in row.items():
                    if value is None:
                        continue
                    # Try to parse float if possible
                    try:
                        if '.' in value or 'e' in value.lower():
                            parsed_row[key] = float(value)
                        else:
                            parsed_row[key] = int(value)
                    except ValueError:
                        parsed_row[key] = value.strip()
            if row_count != 1:
                raise ValueError("The file must contain exactly one row of values.")                
            
        return parsed_row