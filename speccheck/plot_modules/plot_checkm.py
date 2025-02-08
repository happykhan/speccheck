import plotly.express as px
import plotly.offline as pyo


class Plot_Checkm:
    def __init__(self, df):
        self.df = df

    def plot(self):
        # Create a plot for # contigs (>= 1000 bp) group by species
        html_fragment = "<h2>CheckM Plots</h2>"
        fig = px.box(
            self.df,
            x="species",
            y="Contamination",
            color="species",
            title="Box and Whisker Plot of Contamination by Species",
            points="all",
            hover_data=[self.df.index]
        )
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")
        fig = px.box(
            self.df,
            x="species",
            y="Completeness",
            color="species",
            title="Box and Whisker Plot of Completeness by Species",
        )
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        return html_fragment