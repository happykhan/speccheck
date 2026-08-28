from html import escape

import pandas as pd

from speccheck.plot_modules.svg_charts import render_species_bar_chart
from speccheck.report_tables import dataframe_to_interactive_table, status_label


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
                html_fragment += f"<li>{escape(str(species))}: {species_count} sample(s)</li>"
            html_fragment += "</ul></div>"
        else:
            html_fragment += (
                '<div class="status-note pass"><p><strong>Single-species assignment:</strong> '
                f"{escape(str(self.df['speciesName'].unique()[0]))} across all samples.</p></div>"
            )

        if "qc_status" in self.df:
            statuses = self.df["qc_status"].map(status_label)
        elif "all_checks_passed" in self.df:
            statuses = self.df["all_checks_passed"].map(status_label)
        else:
            statuses = pd.Series("NOT_EVALUATED", index=self.df.index)
        exceptions = self.df.loc[statuses != "PASS", ["speciesName", "confidence"]].copy()
        if exceptions.empty:
            html_fragment += "<p>No Speciator exceptions require review.</p>"
        else:
            exceptions["QC"] = statuses.loc[exceptions.index]
            exceptions.index.name = "Sample"
            html_fragment += (
                f"<p><strong>{len(exceptions)} assignment exceptions require review.</strong></p>"
                + dataframe_to_interactive_table(
                    exceptions.reset_index(),
                    "speciator-exceptions",
                    interactive=self.df.attrs.get("interactive_tables", True),
                    page_size=25,
                )
            )

        species_status_counts = (
            pd.DataFrame(
                {"species": self.df["speciesName"], "status": statuses},
                index=self.df.index,
            )
            .groupby(["species", "status"], dropna=False)
            .size()
            .unstack(fill_value=0)
        )
        html_fragment += render_species_bar_chart(
            self.df["speciesName"].value_counts(),
            title="Species distribution by Speciator QC",
            status_counts=species_status_counts,
        )
        html_fragment += "</section>"
        return html_fragment
