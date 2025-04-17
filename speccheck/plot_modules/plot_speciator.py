import plotly.express as px
import plotly.offline as pyo


class Plot_Speciator:
    def __init__(self, df):
        self.df = df

    def plot(self):
        """
        Generate a visualization of Speciator results as an HTML fragment.

        Returns:
            str: HTML fragment containing the Speciator header and pie chart visualization
        """
        html_fragment = "<h2>Speciator</h2>"
        # Add a short description for speciator 
        html_fragment += "<p>Speciator is a tool for assigning species to assembled genomes.</p>"
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
        # Create a stacked bar chart for all_checks_passed grouped by species
        species_count = self.df['speciesName'].value_counts().reset_index()
        species_count.columns = ['speciesName', 'count']
        species_fig = px.pie(
            species_count,
            values='count',
            names='speciesName',
            title='Distribution of Species in Dataset',
            labels={'speciesName': 'Species Name', 'count': 'Count'}
        )
        species_fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(species_fig, include_plotlyjs=False, output_type="div")

        return html_fragment

