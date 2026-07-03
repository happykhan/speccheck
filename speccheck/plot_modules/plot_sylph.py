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
        status = self.df["all_checks_passed"].astype(str).str.lower()
        passed_mask = status.isin(["passed", "true", "1", "yes"])
        if passed_mask.sum() == len(self.df):
            return (
                '<div class="status-note pass"><p><strong>Pass:</strong> '
                "all samples passed the Sylph checks.</p></div>"
            )

        items = []
        for col in self.df.columns:
            if col.endswith(".check") and col != "all_checks_passed":
                col_series = self.df[col].astype(str).str.lower()
                col_pass_mask = col_series.isin(["passed", "true", "1", "yes"])
                fail_count = len(self.df) - int(col_pass_mask.sum())
                if fail_count > 0:
                    col_name = col.split(".")[0]
                    items.append(f"<li>{fail_count} sample(s) failed the {col_name} check.</li>")
        return (
            '<div class="status-note fail"><p><strong>Attention:</strong> '
            "one or more samples failed Sylph QC.</p><ul>" + "".join(items) + "</ul></div>"
        )

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
            '<div class="table-container"><table class="table report-table"><thead><tr>'
            "<th>Sample</th><th>Top species</th><th>Top species ANI</th><th># genomes</th>"
            "<th>All detected species</th><th>QC</th></tr></thead><tbody>"
        )

        for idx, row in self.df.iterrows():
            row = {k: str(v) if v is not None else "N/A" for k, v in row.items()}
            all_species = row.get("species_name", "").split(";")
            all_abundances = row.get("taxonomic_abundances", "").split(";")
            species_breakdown = "<br>".join(
                [f"{s}: {a}%" for s, a in zip(all_species, all_abundances, strict=False) if s]
            )
            all_checks_val = str(row.get("all_checks_passed", "")).lower()
            all_checks_passed = all_checks_val in ["passed", "true", "1", "yes"]
            qc_label = "PASSED" if all_checks_passed else "FAILED"
            qc_class = "qc-pass" if all_checks_passed else "qc-fail"

            html_fragment += (
                "<tr>"
                f"<td>{idx}</td>"
                f"<td>{row.get('top_species', 'N/A')}</td>"
                f"<td>{row.get('top_adjusted_ani', 'N/A')}</td>"
                f"<td>{row.get('number_of_genomes', 'N/A')}</td>"
                f"<td>{species_breakdown}</td>"
                f'<td class="{qc_class}">{qc_label}</td>'
                "</tr>"
            )

        html_fragment += "</tbody></table></div></section>"
        return html_fragment
