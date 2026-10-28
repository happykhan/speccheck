from speccheck.plot_modules.svg_charts import render_scatter_chart
from speccheck.report_tables import tool_status_note


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
        return tool_status_note(self.df, "CheckM")

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
