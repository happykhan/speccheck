import plotly.express as px
import plotly.offline as pyo


class Plot_Ariba:
    def __init__(self, df):
        self.df = df

    def plot(self):
        # Create a plot for # contigs (>= 1000 bp) group by species
        html_fragment = "<h2>Ariba Plots</h2>"
        fig = px.bar(
            self.df,
            x=self.df.index,
            y="percent",
            color="species",
            title="Bar Chart of Allele Percent by Species",
            hover_data=[self.df.index]
        )
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        return html_fragment