import plotly.express as px
import plotly.offline as pyo


class Plot_Quast:
    def __init__(self, df):
        self.df = df
        self.description = "QUAST (Quality Assessment Tool for Genome Assemblies) evaluates genome assemblies by providing metrics such as N50, GC content, and the number of contigs to assess assembly quality."
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
        )

        # Check if there is only one unique species
        if self.df["species"].nunique() == 1:
            fig.update_layout(showlegend=False)
        else:
            fig.update_layout(hovermode="closest", legend_title=color.title())
        fig.update_layout(height=760)
        return pyo.plot(fig, include_plotlyjs=False, output_type="div")

    def plot(self):
        info = self.summary()
        html_fragment = f"<h2 id=\"{info.get('name').lower()}\">{info.get('name')}</h2>"
        # Add explanation text
        html_fragment += f"""
        <p>QUAST (Quality Assessment Tool for Genome Assemblies) is a tool used to evaluate genome assemblies.
        It provides various metrics such as N50, GC content, and the number of contigs to assess the quality of assemblies (<a href="{info.get('citation')}">ref</a>).
        For more information, visit <a href="{info.get('url')}">{info.get('name')}</a>.</p>
        </p>
        """
        # Add a summary of the analysis
        status = self.df["all_checks_passed"].astype(str).str.lower()
        passed_mask = status.isin(["passed", "true", "1", "yes"])  # add values you expect

        # If any sample did not pass, add summary
        if passed_mask.sum() < len(self.df):
            html_fragment += """
            <p>In this analysis:</p>
            <ul>
            """
            for col in self.df.columns:
                if col.endswith(".check") and col != "all_checks_passed":
                    fail_count = len(self.df) - int(self.df[col].sum())
                    col_name = col.split(".")[0]
                    if fail_count > 0:
                        html_fragment += f'<li><span style="color: red; font-weight: bold;">❌</span> Number of samples that failed due to {col_name}: {fail_count}</li>'
                    else:
                        html_fragment += f'<li><span style="color: green; font-weight: bold;">✓</span> All samples that passed {col_name} check.</li>'
            html_fragment += """
            </ul>
            """
        else:
            html_fragment += """
            <p><span style="color: green; font-weight: bold;">✓</span> All samples passed quality checks.</p>
            """
        html_fragment += self._make_scatter_plot(
            col="N50",
            row="Total length (>= 0 bp)",
            color="species",
            title="Distribution of N50 vs Total length",
        )
        html_fragment += self._make_scatter_plot(
            col="# contigs (>= 0 bp)",
            row="Largest contig",
            color="species",
            title="Distribution of # contigs vs largest contig size",
        )
        # Add a short explanation of what N50 is,  as a note.
        # Add a short explanation of what N50 is, as a note.
        html_fragment += """
        <p><strong>Note:</strong> N50 is a metric used to assess the quality of genome assemblies.
        It represents the length of the shortest contig for which the sum of contigs of that length or longer
        covers at least 50% of the total assembly length. A higher N50 value indicates better assembly quality.</p>
        """
        return html_fragment
