import pandas as pd

from speccheck.report_tables import dataframe_to_interactive_table, status_label


class Plot_Ariba:
    def __init__(self, df):
        self.df = df
        self.description = "ARIBA summarizes resistance or genotyping hits from sequencing reads."
        self.url = "https://github.com/sanger-pathogens/ariba"
        self.name = "ARIBA"
        self.citation = "https://pmc.ncbi.nlm.nih.gov/articles/PMC5695208/"

    def summary(self):
        return {
            "description": self.description,
            "url": self.url,
            "name": self.name,
            "citation": self.citation,
        }

    def plot(self):
        summary = self.summary()
        html_fragment = (
            '<section class="software-block">'
            '<div class="software-kicker">Genotyping summary</div>'
            '<h2 id="ariba">ARIBA</h2>'
            f'<p class="software-lede"><a href="{summary["url"]}" target="_blank"><strong>ARIBA</strong></a> '
            "identifies resistance genes and variant calls from read data. "
            f'<a href="{summary["citation"]}" target="_blank">Citation</a>.</p>'
        )
        if len(self.df) > 0:
            total_samples = len(self.df)
            if "qc_status" in self.df:
                statuses = self.df["qc_status"].map(status_label)
            elif "all_checks_passed" in self.df:
                statuses = self.df["all_checks_passed"].map(status_label)
            elif "percent.check" in self.df:
                statuses = self.df["percent.check"].map(status_label)
            else:
                statuses = pd.Series("PASS", index=self.df.index)
            passed_samples = int((statuses == "PASS").sum())
            warn_samples = int((statuses == "WARN").sum())
            failed_samples = int((statuses == "FAIL").sum())
            not_evaluated_samples = int((statuses == "NOT_EVALUATED").sum())
            html_fragment += (
                '<div class="status-note">'
                f"<p><strong>Summary:</strong> {total_samples} samples, "
                f'<span class="qc-pass-text">{passed_samples} passed</span>, '
                f'<span class="qc-warn-text">{warn_samples} warning</span>, '
                f'<span class="qc-fail-text">{failed_samples} failed</span>, and '
                f'<span class="qc-not-evaluated-text">{not_evaluated_samples} not evaluated</span>.'
                "</p></div>"
            )
            exception_columns = [
                column
                for column in ("species", "passed", "total", "percent", "percent.check")
                if column in self.df
            ]
            exceptions = self.df.loc[statuses != "PASS", exception_columns].copy()
            if exceptions.empty:
                html_fragment += "<p>No ARIBA exceptions require review.</p>"
            else:
                exceptions.index.name = "Sample"
                exceptions = exceptions.rename(
                    columns={"percent": "Percent (%)", "percent.check": "Percent check"}
                )
                html_fragment += (
                    f"<p><strong>{len(exceptions)} ARIBA exceptions require review.</strong></p>"
                    + dataframe_to_interactive_table(
                        exceptions.reset_index(),
                        "ariba-exceptions",
                        interactive=self.df.attrs.get("interactive_tables", True),
                        page_size=25,
                    )
                )
        else:
            html_fragment += "<p>No ARIBA results were available.</p>"
        html_fragment += "</section>"
        return html_fragment
