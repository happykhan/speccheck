import plotly.express as px
import plotly.offline as pyo


class Plot_Sylph:
    def __init__(self, df):
        self.df = df

    def plot(self):
        # Create a plot for # contigs (>= 1000 bp) group by species
        html_fragment = "<h2>Sylph Plots</h2>"
        html_fragment += """
        <p>Sylph is a tool for phylogenetic placement of microbiome samples. 
        It analyzes sequencing data and provides metrics to understand the taxonomic composition of microbial communities.</p>
        """
        if int(self.df['all_checks_passed'].sum()) < len(self.df):
            html_fragment += """
            <p>In this analysis:</p>
            <ul>
            """
            for col in self.df.columns:
                if col.endswith(".check") and col != "all_checks_passed":
                    fail_count = len(self.df) - int(self.df[col].sum())
                    col_name = col.split(".")[0]
                    if fail_count > 0:
                        html_fragment += f"<li><span style=\"color: red; font-weight: bold;\">❌</span> Number of samples that failed due to {col_name}: {fail_count}</li>"
                    else:
                        html_fragment += f"<li><span style=\"color: green; font-weight: bold;\">✓</span> All samples that passed {col_name} check.</li>"
            html_fragment += """
            </ul>
            """
        else:
            html_fragment += """
            <p><span style="color: green; font-weight: bold;">✓</span> All samples passed quality checks.</p>
            """

        


        return html_fragment