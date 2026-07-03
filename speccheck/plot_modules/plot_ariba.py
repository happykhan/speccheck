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
            '<div class="table-container"><table class="table report-table"><thead><tr>'
            "<th>Sample</th><th>Species</th><th>Passed</th><th>Total</th>"
            "<th>Percent (%)</th><th>Percent check</th></tr></thead><tbody>"
        )

        for idx, row in self.df.iterrows():
            sample_id = str(idx)
            species = row.get("species", "N/A")
            passed = row.get("passed", "N/A")
            total = row.get("total", "N/A")
            percent = row.get("percent", "N/A")
            percent_check = row.get("percent.check", "N/A")
            percent_display = (
                f"{percent:.1f}%" if isinstance(percent, (int, float)) else str(percent)
            )
            if percent_check is False:
                percent_check_display = '<span class="qc-fail">FAILED</span>'
            elif percent_check:
                percent_check_display = '<span class="qc-pass">PASSED</span>'
            else:
                percent_check_display = str(percent_check)

            html_fragment += (
                "<tr>"
                f"<td>{sample_id}</td><td>{species}</td><td>{passed}</td><td>{total}</td>"
                f"<td>{percent_display}</td><td>{percent_check_display}</td>"
                "</tr>"
            )

        html_fragment += "</tbody></table></div>"
        if len(self.df) > 0:
            total_samples = len(self.df)
            passed_samples = (
                self.df["all_checks_passed"].sum() if "all_checks_passed" in self.df.columns else 0
            )
            failed_samples = total_samples - passed_samples
            html_fragment += (
                '<div class="status-note">'
                f"<p><strong>Summary:</strong> {total_samples} samples, "
                f'<span class="qc-pass-text">{passed_samples} passed</span>, '
                f'<span class="qc-fail-text">{failed_samples} failed</span>.</p></div>'
            )
        html_fragment += "</section>"
        return html_fragment
