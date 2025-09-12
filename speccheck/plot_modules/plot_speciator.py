import plotly.express as px
import plotly.offline as pyo


class Plot_Speciator:
    def __init__(self, df):
        self.df = df
        self.description = "A tool for classifying or analyzing species (speciation) in a dataset."
        self.url = "https://cgps.gitbook.io/pathogenwatch/technical-descriptions/species-assignment/speciator"      
        self.name = 'Speciator'

    def summary(self):
        return {'description': self.description, 'url': self.url, 'name': self.name}

    def plot(self):
        """
        Generate a visualization of Speciator results as an HTML fragment.

        Returns:
            str: HTML fragment containing the Speciator header and pie chart visualization
        """
        summary = self.summary()
        html_fragment = "<h2 id=\"speciator\">Speciator</h2>"
        # Add a short description for speciator
        html_fragment += (
            '<p>Speciator is a tool for assigning species to assembled genomes. '
            f'Learn more at <a href="{summary["url"]}" target="_blank">Speciator documentation</a>.</p>'
        )
        # Add a summary of species distribution
        if len(self.df['speciesName'].unique()) > 1:
            html_fragment += """
            <p>In this analysis:</p>
            <ul>
            """
            for species in self.df['speciesName'].unique():
                species_count = self.df[self.df['speciesName'] == species].shape[0]
                html_fragment += f"<li><span style=\"color: blue; font-weight: bold;\">🔹</span> Number of samples assigned to <strong>{species}</strong>: {species_count}</li>"
            html_fragment += """
            </ul>
            """
        else:
            html_fragment += """
            <p><span style="color: green; font-weight: bold;">✓</span> All samples were assigned to a single species: 
            <strong>{}</strong>.</p>
            """.format(self.df['speciesName'].unique()[0])
            html_fragment += """<p>Hopefully, this is the one your were expecting!</p>"""
        # Create a table of speciator results 
        html_fragment += "<div class=\"table-container\">"
        # Only include columns taxid, mashDistance, pValue, matchingHashes, confidence, source.
        columns_to_include = ['speciesName', 'taxId', 'mashDistance', 'pValue', 'matchingHashes', 'confidence']
        table_df = self.df[columns_to_include].copy()
        # Rename columns to be more user-friendly
        table_df.rename(columns={
            'speciesName': 'Species Name',
            'taxId': 'Tax ID',
            'mashDistance': 'Mash Distance',
            'pValue': 'P-Value',
            'matchingHashes': 'Matching Hashes',
            'confidence': 'Confidence',
        }, inplace=True)
        styled_table = table_df.style.set_table_attributes('class="table is-striped is-hover is-fullwidth"')

        html_fragment += styled_table.to_html()
        html_fragment += "</div>"

        # Create a stacked bar chart for all_checks_passed grouped by species
        species_count = table_df['Species Name'].value_counts().reset_index()
        species_count.columns = ['Species Name', 'Count']
        species_fig = px.pie(
            species_count,
            values='Count',
            names='Species Name',
            title='Distribution of Species in Dataset',
            labels={'Species Name': 'Species Name', 'Count': 'Count'}
        )
        species_fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(species_fig, include_plotlyjs=False, output_type="div")

        return html_fragment

