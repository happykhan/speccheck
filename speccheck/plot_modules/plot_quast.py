import plotly.express as px
import plotly.offline as pyo


class Plot_Quast:
    def __init__(self, df):
        self.df = df

    def plot(self):
        # Create a plot for # contigs (>= 1000 bp) group by species
        html_fragment = "<h2>Quast Plots</h2>"
        # So if there is only one species. We don't need box plot. 
        # if len(self.df["species"].unique()) == 1:
        #     print(self.df)
        #     # Rename N50.check False to Fail and True to Pass
        #     self.df["# contigs (>= 0 bp).check"] = self.df["# contigs (>= 0 bp).check"].replace({True: "Pass", False: "Fail"})
        #     fig = px.scatter(
        #         self.df,
        #         x="species",
        #         y="# contigs (>= 0 bp)",
        #         color="# contigs (>= 0 bp).check",
        #         title="Scatter Plot of Contigs (>= 0 bp) by Species",
        #         hover_data=[self.df.index],
        #         color_discrete_map={"Pass": "blue", "Fail": "red"}
        #     )
        #     fig.update_xaxes(title_text="Species")
        #     html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        # else:
        fig = px.box(
            self.df,
            x="species",
            y="# contigs (>= 0 bp)",
            color="species",
            title="Box and Whisker Plot of Contigs (>= 0 bp) by Species",
            points="all",
            hover_data=[self.df.index]
        )
        fig.update_xaxes(title_text="Species")
        fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")
        fig = px.box(
            self.df,
            x="species",
            y="N50",
            color="species",
            title="Box and Whisker Plot of N50 by Species",
            points="all",
            hover_data=[self.df.index],
            
        )
        fig.update_layout(hovermode="x unified")
        fig.update_xaxes(title_text="Species")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        fig = px.box(
            self.df,
            x="species",
            y="# N's per 100 kbp",
            color="species",
            title="Box and Whisker Plot of # N's per 100 kbp by Species",
            points="all",
            hover_data=[self.df.index]            
        )
        fig.update_xaxes(title_text="Species")
        fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        fig = px.box(
            self.df,
            x="species",
            y="GC (%)",
            color="species",
            title="Box and Whisker Plot of GC (%) by Species",
            points="all",
            hover_data=[self.df.index]
        )
        fig.update_xaxes(title_text="Species")
        fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")
        fig = px.box(
            self.df,
            x="species",
            y="Total length (>= 0 bp)",
            color="species",
            title="Box and Whisker Plot of Total Length (>= 0 bp) by Species",
            points="all",
            hover_data=[self.df.index]
        )
        fig.update_xaxes(title_text="Species")
        fig.update_layout(hovermode="x unified")
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")


        return html_fragment

