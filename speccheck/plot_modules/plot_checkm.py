import plotly.express as px
import plotly.offline as pyo


def _is_passed(value):
    return str(value).strip().lower() in {"passed", "pass", "true", "1", "yes"}


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

    def _apply_layout(self, fig, height):
        fig.update_layout(
            height=height,
            paper_bgcolor="#ffffff",
            plot_bgcolor="#f6f8fa",
            font={"color": "#1f2933"},
            margin={"l": 56, "r": 24, "t": 64, "b": 56},
        )
        fig.update_xaxes(gridcolor="#d7dde3", zerolinecolor="#aeb8c2")
        fig.update_yaxes(gridcolor="#d7dde3", zerolinecolor="#aeb8c2")
        return fig

    def _make_scatter_plot(self, col, row, color, title):
        fig = px.scatter(
            self.df,
            y=col,
            x=row,
            color=color,
            marginal_x="violin",
            marginal_y="violin",
            title=title,
            hover_name="sample_id" if "sample_id" in self.df.columns else None,
            hover_data={"species": False},
            color_discrete_sequence=["#1f5f8b", "#667085", "#2f6f5e", "#8a6f3d"],
        )
        if self.df["species"].nunique() == 1:
            fig.update_layout(showlegend=False)
        else:
            fig.update_layout(hovermode="closest", legend_title=color.title())
        self._apply_layout(fig, 700)
        return f'<div class="chart-frame">{pyo.plot(fig, include_plotlyjs=False, output_type="div")}</div>'

    def _status_html(self):
        status = self.df["all_checks_passed"].astype(str).str.lower()
        passed_mask = status.isin(["passed", "true", "1", "yes"])
        if passed_mask.sum() == len(self.df):
            return (
                '<div class="status-note pass"><p><strong>Pass:</strong> '
                "all samples passed the CheckM QC checks.</p></div>"
            )

        items = []
        for col in self.df.columns:
            if col.endswith(".check") and col != "all_checks_passed":
                fail_count = len(self.df) - int(self.df[col].map(_is_passed).sum())
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
                color="species",
                title="Contamination vs completeness",
            )
            + self._make_scatter_plot(
                col="GC_Content",
                row="Genome_Size",
                color="species",
                title="Estimated genome size vs GC content",
            )
            + self._make_scatter_plot(
                col="Contig_N50",
                row="Total_Contigs",
                color="species",
                title="Contig count vs N50",
            )
            + "</section>"
        )
        return html_fragment
