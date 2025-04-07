import plotly.express as px
import plotly.offline as pyo


class Plot_Speciator:
    def __init__(self, df):
        self.df = df

    def plot(self):
        html_fragment = "<h2>Speciator</h2>"
        # Create a stacked bar chart for all_checks_passed grouped by species
        species_count = self.df['speciesName'].value_counts().reset_index()
        species_count.columns = ['speciesName', 'count']

        species_fig = px.bar(
            species_count,
            x='speciesName',
            y='count',
            title='Count of Each Species in Dataset',
            labels={'speciesName': 'Species Name', 'count': 'Count'},
            color='speciesName'
        )
        species_fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(species_fig, include_plotlyjs=False, output_type="div")

        return html_fragment

