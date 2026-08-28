from html import escape

import pandas as pd

from speccheck.report_tables import dataframe_to_interactive_table, status_label


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
        status = self._statuses()
        passed_mask = status == "PASS"
        if passed_mask.sum() == len(self.df):
            return (
                '<div class="status-note pass"><p><strong>Pass:</strong> '
                "all samples passed the Sylph checks.</p></div>"
            )

        items = []
        for col in self.df.columns:
            if col.endswith((".check", ".status")):
                fail_count = int((self.df[col].map(status_label) == "FAIL").sum())
                if fail_count > 0:
                    col_name = col.split(".")[0]
                    items.append(f"<li>{fail_count} sample(s) failed the {col_name} check.</li>")
        return (
            '<div class="status-note fail"><p><strong>Attention:</strong> '
            "one or more samples failed Sylph QC.</p><ul>" + "".join(items) + "</ul></div>"
        )

    def _statuses(self):
        if "qc_status" in self.df:
            return self.df["qc_status"].map(status_label)
        if "all_checks_passed" in self.df:
            return self.df["all_checks_passed"].map(status_label)
        return pd.Series("PASS", index=self.df.index)

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
