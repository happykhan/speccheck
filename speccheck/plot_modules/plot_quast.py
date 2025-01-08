import plotly.express as px
import plotly.offline as pyo


class Plot_Quast:
    def __init__(self, df):
        self.df = df

    def plot(self):
        # Create a plot for # contigs (>= 1000 bp) group by species
        html_fragment = "<h2>Quast Plots</h2>"
        fig = px.box(
            self.df,
            x="species",
            y="# contigs (>= 1000 bp)",
            color="species",
            title="Box and Whisker Plot of Contigs (>= 1000 bp) by Species",
        )
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")
        fig = px.box(
            self.df,
            x="species",
            y="N50",
            color="species",
            title="Box and Whisker Plot of N50 by Species",
        )
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        fig = px.box(
            self.df,
            x="species",
            y="# N's per 100 kbp",
            color="species",
            title="Box and Whisker Plot of # N's per 100 kbp by Species",
        )
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        fig = px.box(
            self.df,
            x="species",
            y="GC (%)",
            color="species",
            title="Box and Whisker Plot of GC (%) by Species",
        )
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")
        fig = px.box(
            self.df,
            x="species",
            y="Total length (>= 0 bp)",
            color="species",
            title="Box and Whisker Plot of Total Length (>= 0 bp) by Species",
        )
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")


        return html_fragment

