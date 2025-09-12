
import plotly.express as px
import plotly.offline as pyo


class Plot_Checkm:
    def __init__(self, df):
        self.df = df
        self.description = "CheckM is a tool used to assess the quality of genome bins by evaluating their completeness and contamination. It provides insights into the reliability of genome assemblies."
        self.url = "https://github.com/Ecogenomics/CheckM"
        self.name = 'CheckM'
        self.citation = 'https://genome.cshlp.org/content/25/7/1043'

    def summary(self):
        """
        Returns a summary of the object's key attributes.

        Returns:
            dict: A dictionary containing the description, URL, name, and citation of the object.
        """
        return {'description': self.description, 'url': self.url, 'name': self.name, 'citation': self.citation}        
        
    def _make_scatter_plot(self, col, row, color, title):
        fig = px.scatter(
            self.df,
            y=col,
            x=row,
            color=color,
            marginal_x="violin",
            marginal_y="violin",
            title=title,
            hover_data=[self.df.index],
        )
                
        # Check if there is only one unique species
        if self.df["species"].nunique() == 1:
            fig.update_layout(showlegend=False)  # Hide legend if only one species
        else:
            fig.update_layout(hovermode="closest", legend_title=color.title())
        return pyo.plot(fig, include_plotlyjs=False, output_type="div")

    def plot(self):
        # Create a scatter plot for Contamination vs Completeness with violin plots
        html_fragment = "<h2 id=\"checkm\">CheckM</h2>"
        summary = self.summary()
        # Add a short description for CheckM
        html_fragment += f"""
        <p>
        <a href="{summary["url"]}" target="_blank"><b>CheckM</b></a> is a tool used to assess the quality of genome bins by evaluating their completeness and contamination.
        It provides insights into the reliability of genome assemblies.
        [<a href="{summary["citation"]}" target="_blank">citation</a>]
        </p>
        """
        html_fragment += """
        <p>
        When CheckM evaluates contigs, it first estimates its taxonomic lineage using a reference tree built from conserved marker genes. This lineage (marker lineage) is used to select a set of marker genes specific to that lineage (e.g., Bacteria &gt; Proteobacteria &gt; Gammaproteobacteria). These marker genes are chosen because they are typically single-copy and universally present in that lineage. This is used to compute:
        <ul>
            <li><b>Completeness</b>: how many expected marker genes are present as a percentage.</li>
            <li><b>Contamination</b>: how many are present in multiple copies (as a percentage), suggesting contamination or strain heterogeneity.</li>
        </ul>
        Speccheck will check if the marker lineage matches the expected species lineage, and if the completeness and contamination values are within acceptable ranges. The expected ranges are explained <a href="https://happykhan.github.io/genomeqc/" target="_blank">here</a>.
        </p>
        """
        # Add a summary of the analysis
        if int(self.df["all_checks_passed"].sum()) < len(self.df):
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
                        html_fragment += f'<li><span style="color: green; font-weight: bold;">✓</span> All samples passed {col_name} check.</li>'
            html_fragment += """
            </ul>
            """
        else:
            html_fragment += """
            <p><span style="color: green; font-weight: bold;">✓</span> All samples passed quality checks.</p>
            """
        print(self.df.columns)
        html_fragment += self._make_scatter_plot(
            col="Completeness",
            row="Contamination",
            color="species",
            title="Contamination vs Completeness",
        )
        html_fragment += self._make_scatter_plot(
            col="GC",
            row="Genome size (bp)",
            color="species",
            title="Estimated genome size vs GC content",
        )
        html_fragment += self._make_scatter_plot(
            col="N50 (contigs)",
            row="# contigs",
            color="species",
            title="Number of contigs vs N50 ",
        )

        return html_fragment
