import re
import csv 

class Ariba():

    def __init__(self, file_path):
        self.file_path = file_path
    
    @property
    def has_valid_filename(self):
        return self.file_path.endswith(".tsv")

    @property
    def has_valid_fileformat(self):

        required_headers = [
            'gene', 'allele', 'cov', 'pc', 'ctgs', 'depth', 'hetmin', 'hets'
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
            result = {'passed': 0, 'total': 0, 'percent': 0}   
            for row in reader:
                # if allele does not have *, then passed 
                if '*' not in row['allele']:
                    result['passed'] += 1
                result['total'] += 1
            result['percent'] = result['passed'] / result['total'] * 100    
        return result