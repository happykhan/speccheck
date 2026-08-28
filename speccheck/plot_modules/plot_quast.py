from speccheck.plot_modules.svg_charts import render_scatter_chart
from speccheck.report_tables import status_label


def _status_series(df):
    column = "qc_status" if "qc_status" in df.columns else "all_checks_passed"
    return df[column].map(status_label)


class Plot_Quast:
    def __init__(self, df):
        self.df = df
        self.description = (
            "QUAST evaluates assembly contiguity, size, GC content, and related assembly metrics."
        )
        self.url = "https://quast.sourceforge.net/"
        self.name = "QUAST"
        self.citation = "https://doi.org/10.1093/bioinformatics/btt086"

    def summary(self):
        return {
            "description": self.description,
            "url": self.url,
            "name": self.name,
            "citation": self.citation,
        }

    def _make_scatter_plot(self, col, row, title):
        return render_scatter_chart(
            self.df,
            y_column=col,
            x_column=row,
            y_label="N50 (bp)",
            x_label="Total assembly length (bp)",
            title=title,
        )

    def _status_html(self):
        status = _status_series(self.df)
        passed_mask = status == "PASS"
        if passed_mask.sum() == len(self.df):
            return (
                '<div class="status-note pass"><p><strong>Pass:</strong> '
                "all samples passed the QUAST assembly checks.</p></div>"
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
            "one or more samples failed QUAST assembly QC.</p><ul>" + "".join(items) + "</ul></div>"
        )

    def plot(self):
        info = self.summary()
        html_fragment = (
            '<section class="software-block">'
            '<div class="software-kicker">Assembly contiguity</div>'
            f'<h2 id="{info["name"].lower()}">{info["name"]}</h2>'
            f'<p class="software-lede"><a href="{info["url"]}" target="_blank"><strong>QUAST</strong></a> '
            "summarizes contiguity and assembly size metrics such as N50, contig count, GC content, "
            f'and total length. <a href="{info["citation"]}" target="_blank">Citation</a>.</p>'
            '<div class="note-panel"><p>N50 captures the contig length threshold at which half of the assembly '
            "is contained in contigs of that size or longer. Larger values generally indicate better contiguity.</p></div>"
            f"{self._status_html()}"
            + self._make_scatter_plot(
                col="N50",
                row="Total length (>= 0 bp)",
                title="N50 vs total assembly length",
            )
            + "</section>"
        )
        return html_fragment
