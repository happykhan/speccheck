from html import escape

from speccheck.report_tables import (
    dataframe_to_interactive_table,
    tool_status_note,
    tool_status_series,
)


class Plot_Sylph:
    def __init__(self, df):
        self.df = df
        self.description = (
            "Sylph estimates dominant species composition and abundance across samples."
        )
        self.url = "https://github.com/bluenote-1577/sylph"
        self.name = "Sylph"
        self.citation = "https://www.nature.com/articles/s41587-024-02412-y"

    def summary(self):
        return {
            "description": self.description,
            "url": self.url,
            "name": self.name,
            "citation": self.citation,
        }

    def _status_html(self):
        return tool_status_note(self.df, "Sylph")

    def _statuses(self):
        return tool_status_series(self.df)

    def plot(self):
        summary = self.summary()
        html_fragment = (
            '<section class="software-block">'
            '<div class="software-kicker">Taxonomic abundance</div>'
            '<h2 id="sylph">Sylph</h2>'
            f'<p class="software-lede"><a href="{summary["url"]}" target="_blank"><strong>Sylph</strong></a> '
            "summarizes dominant species calls and abundance-style signals from the sample set. "
            f'<a href="{summary["citation"]}" target="_blank">Citation</a>.</p>'
            f"{self._status_html()}"
        )
        top_species = self.df.get("top_species")
        if top_species is not None:
            common = top_species.dropna().astype(str).value_counts().head(5)
            if not common.empty:
                html_fragment += '<div class="compact-counts"><strong>Dominant calls:</strong><ul>'
                html_fragment += "".join(
                    f"<li>{escape(species)}: {int(count)} sample(s)</li>"
                    for species, count in common.items()
                )
                html_fragment += "</ul></div>"

        statuses = self._statuses()
        exception_columns = [
            column
            for column in ("top_species", "top_adjusted_ani", "number_of_genomes")
            if column in self.df
        ]
        exceptions = self.df.loc[statuses != "PASS", exception_columns].copy()
        if exceptions.empty:
            html_fragment += "<p>No Sylph exceptions require review.</p>"
        else:
            exceptions["QC"] = statuses.loc[exceptions.index]
            exceptions.index.name = "Sample"
            html_fragment += (
                f"<p><strong>{len(exceptions)} Sylph exceptions require review.</strong></p>"
                + dataframe_to_interactive_table(
                    exceptions.reset_index(),
                    "sylph-exceptions",
                    interactive=self.df.attrs.get("interactive_tables", True),
                    page_size=25,
                )
            )
        html_fragment += "</section>"
        return html_fragment
