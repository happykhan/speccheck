class Plot_Ariba:
    def __init__(self, df):
        self.df = df
        self.description = "ARIBA is a tool for genotyping from sequencing reads."
        self.url = "https://github.com/sanger-pathogens/ariba"
        self.name = 'ARIBA'
        self.citation = 'https://pmc.ncbi.nlm.nih.gov/articles/PMC5695208/'

    def summary(self):
        return {'description': self.description, 'url': self.url, 'name': self.name, 'citation': self.citation}

    def plot(self):
        # Create a summary table instead of a bar chart
        html_fragment = "<h2 id=\"ariba\">Ariba Results</h2>"
        
        # Add description
        html_fragment += """
        <p>ARIBA (Antimicrobial Resistance Identification By Assembly) identifies antimicrobial resistance genes 
        and variants from sequencing reads. The table below summarizes the results for each sample.</p>
        """
        
        # Create table HTML
        html_fragment += """
        <div class="table-container">
            <table class="table is-striped is-fullwidth">
                <thead>
                    <tr>
                        <th>Sample</th>
                        <th>Species</th>
                        <th>Passed</th>
                        <th>Total</th>
                        <th>Percent (%)</th>
                        <th>Percent Check</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add data rows
        for idx, row in self.df.iterrows():
            sample_name = str(idx)
            species = row.get('species', 'N/A')
            passed = row.get('passed', 'N/A')
            total = row.get('total', 'N/A')
            percent = row.get('percent', 'N/A')
            percent_check = row.get('percent.check', 'N/A')
            
            # Format percent with 1 decimal place if it's a number
            if isinstance(percent, (int, float)):
                percent_display = f"{percent:.1f}%"
            else:
                percent_display = str(percent)
            
            # Color code the check results
            percent_check_display = "✓" if percent_check else "❌" if percent_check is False else str(percent_check)
            
            percent_check_color = "color: green;" if percent_check else "color: red;" if percent_check is False else ""
            
            html_fragment += f"""
                    <tr>
                        <td>{sample_name}</td>
                        <td>{species}</td>
                        <td>{passed}</td>
                        <td>{total}</td>
                        <td>{percent_display}</td>
                        <td style="{percent_check_color}">{percent_check_display}</td>
                    </tr>
            """
        
        html_fragment += """
                </tbody>
            </table>
        </div>
        """
        
        # Add summary statistics as a single text line
        if len(self.df) > 0:
            total_samples = len(self.df)
            passed_samples = self.df['all_checks_passed'].sum() if 'all_checks_passed' in self.df.columns else 0
            failed_samples = total_samples - passed_samples

            html_fragment += f"""
            <div class="content">
            <p><strong>Summary:</strong> Total samples: {total_samples} | <span style="color: green;">Passed: {passed_samples}</span> | <span style="color: red;">Failed: {failed_samples}</span></p>
            </div>
            """
        
        return html_fragment