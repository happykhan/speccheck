import plotly.express as px
import plotly.offline as pyo


class Plot_Speciator:
    def __init__(self, df):
        self.df = df

    def plot(self):
        html_fragment = "<h2>Speciator</h2>"
        pass_fail_count = self.df['all_checks_passed'].value_counts().reset_index()
        pass_fail_count.columns = ['all_checks_passed', 'count']

        fig_pass_fail = px.pie(
            pass_fail_count,
            names='all_checks_passed',
            values='count',
            title='Proportion of Pass/Fail Samples',
            color='all_checks_passed',
            color_discrete_map={True: 'light green', False: 'light red'}
        )
        
        html_fragment += pyo.plot(fig_pass_fail, include_plotlyjs=False, output_type="div")

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

