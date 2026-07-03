import plotly.express as px
import plotly.offline as pyo


class Plot_Speciator:
    def __init__(self, df):
        self.df = df
        self.description = "Speciator assigns assembled genomes to species."
        self.url = "https://cgps.gitbook.io/pathogenwatch/technical-descriptions/species-assignment/speciator"
        self.name = "Speciator"

    def summary(self):
        return {"description": self.description, "url": self.url, "name": self.name}

    def plot(self):
        summary = self.summary()
        html_fragment = (
            '<section class="software-block">'
            '<div class="software-kicker">Species assignment</div>'
            '<h2 id="speciator">Speciator</h2>'
            f'<p class="software-lede"><a href="{summary["url"]}" target="_blank"><strong>Speciator</strong></a> '
            "assigns each assembly to a species and reports assignment confidence.</p>"
        )
        if len(self.df["speciesName"].unique()) > 1:
            html_fragment += (
                '<div class="status-note fail"><p><strong>Mixed assignments:</strong></p><ul>'
            )
            for species in self.df["speciesName"].unique():
                species_count = self.df[self.df["speciesName"] == species].shape[0]
                html_fragment += f"<li>{species}: {species_count} sample(s)</li>"
            html_fragment += "</ul></div>"
        else:
            html_fragment += (
                '<div class="status-note pass"><p><strong>Single-species assignment:</strong> '
                f'{self.df["speciesName"].unique()[0]} across all samples.</p></div>'
            )

        interactive_tables = self.df.attrs.get("interactive_tables", True)
        table_class = "table report-table"
        if interactive_tables:
            table_class += " js-sort-filter"
        html_fragment += (
            f'<div class="table-container"><table class="{table_class}" id="speciator-results">'
            '<thead><tr><th data-type="string">Species</th><th data-type="string">Confidence</th></tr></thead><tbody>'
        )
        table_df = self.df[["speciesName", "confidence"]].copy()
        for _, row in table_df.iterrows():
            html_fragment += f"<tr><td>{row['speciesName']}</td><td>{row['confidence']}</td></tr>"
        html_fragment += "</tbody></table></div>"

        species_count = table_df["speciesName"].value_counts().reset_index()
        species_count.columns = ["Species Name", "Count"]
        species_fig = px.pie(
            species_count,
            values="Count",
            names="Species Name",
            title="Species distribution",
            labels={"Species Name": "Species", "Count": "Count"},
            color_discrete_sequence=["#1f5f8b", "#667085", "#2f6f5e", "#8a6f3d"],
        )
        species_fig.update_layout(
            hovermode="closest",
            height=560,
            paper_bgcolor="#ffffff",
            font={"color": "#1f2933"},
            margin={"l": 24, "r": 24, "t": 64, "b": 24},
        )
        html_fragment += (
            f'<div class="chart-frame">{pyo.plot(species_fig, include_plotlyjs=False, output_type="div")}</div>'
            "</section>"
        )
        return html_fragment
