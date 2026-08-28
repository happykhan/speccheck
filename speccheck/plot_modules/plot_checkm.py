from speccheck.plot_modules.svg_charts import render_scatter_chart
from speccheck.report_tables import status_label


def _status_series(df):
    column = "qc_status" if "qc_status" in df.columns else "all_checks_passed"
    return df[column].map(status_label)


class Plot_Checkm:
    def __init__(self, df):
        self.df = df
        self.description = (
            "CheckM assesses assembly completeness and contamination using conserved marker genes."
        )
        self.url = "https://github.com/Ecogenomics/CheckM"
        self.name = "CheckM"
        self.citation = "https://genome.cshlp.org/content/25/7/1043"

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
            y_label="Completeness (%)",
            x_label="Contamination (%)",
            title=title,
        )

    def _status_html(self):
        status = _status_series(self.df)
        passed_mask = status == "PASS"
        if passed_mask.sum() == len(self.df):
            return (
                '<div class="status-note pass"><p><strong>Pass:</strong> '
                "all samples passed the CheckM QC checks.</p></div>"
            )

        items = []
        for col in self.df.columns:
            if col.endswith((".check", ".status")):
                fail_count = int((self.df[col].map(status_label) == "FAIL").sum())
                if fail_count > 0:
                    col_name = col.split(".")[0]
                    items.append(f"<li>{fail_count} sample(s) failed the {col_name} check.</li>")
        if not items:
            items.append(
                "<li>At least one sample failed, but no specific sub-check count was available.</li>"
            )
        return (
            '<div class="status-note fail"><p><strong>Attention:</strong> '
            "one or more samples failed CheckM QC.</p><ul>" + "".join(items) + "</ul></div>"
        )

    def plot(self):
        summary = self.summary()
        html_fragment = (
            '<section class="software-block">'
            '<div class="software-kicker">Assembly integrity</div>'
            '<h2 id="checkm">CheckM</h2>'
            f'<p class="software-lede"><a href="{summary["url"]}" target="_blank"><strong>CheckM</strong></a> '
            "estimates completeness and contamination from lineage-specific single-copy markers. "
            f'<a href="{summary["citation"]}" target="_blank">Citation</a>.</p>'
            '<div class="note-panel"><p>Interpretation focuses on marker completeness, contamination, '
            "GC content, and estimated genome size relative to the expected organism profile.</p></div>"
            f"{self._status_html()}"
            + self._make_scatter_plot(
                col="Completeness",
                row="Contamination",
                title="Contamination vs completeness",
            )
            + "</section>"
        )
        return html_fragment
