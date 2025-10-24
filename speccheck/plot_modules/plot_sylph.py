import plotly.express as px
import plotly.offline as pyo


class Plot_Sylph:
    def __init__(self, df):
        self.df = df
        self.description = "Sylph is a tool for phylogenetic placement of microbiome samples, providing metrics to understand the taxonomic composition of microbial communities."
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

    def plot(self):
        # TODO: Improve reporting of **multiple species** per sample.
        # TODO: Add explanation for **why a sample failed**, if applicable.

        # Create a plot for # contigs (>= 1000 bp) group by species
        html_fragment = '<h2 id="sylph">Sylph Plots</h2>'
        summary = self.summary()
        html_fragment += f"""
        <p>Sylph is a tool for phylogenetic placement of microbiome samples. 
        It analyzes sequencing data and provides metrics to understand the taxonomic composition of microbial communities.
        For more information, visit the <a href="{summary.get('url')}" target="_blank">the website</a>. [citation: <a href="{summary.get('citation')}" target="_blank">Sylph paper</a>]</p>
        </p>
        """
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
                        html_fragment += f'<li><span style="color: green; font-weight: bold;">✓</span> All samples that passed {col_name} check.</li>'
            html_fragment += """
            </ul>
            """
        else:
            html_fragment += """
            <p><span style="color: green; font-weight: bold;">✓</span> All samples passed quality checks.</p>
            """
        # Create a table of the dataframe, with the check results
        html_fragment += """
        <div class="table-container">
            <table class="table is-striped is-fullwidth">
                <thead>
                    <tr>
                        <th>Sample</th>
                        <th>Top Species</th>
                        <th>Top Species ANI</th>
                        <th># Genomes</th>
                        <th>All Detected Species</th>
                        <th>All Checks Passed</th>
                    </tr>
                </thead>
                <tbody>
        """

        for idx, row in self.df.iterrows():
            # convert everthing in the row into a string
            row = {k: str(v) if v is not None else "N/A" for k, v in row.items()}
            sample_id = idx
            top_species = row.get("top_species", "N/A")
            top_ani = row.get("top_adjusted_ani", "N/A")
            num_genomes = row.get("number_of_genomes", "N/A")

            # Get all species and abundances for the tooltip
            all_species = row.get("species_name", "").split(";")
            all_abundances = row.get("taxonomic_abundances", "").split(";")

            # Create a formatted list for all species
            species_breakdown = "<br>".join(
                [f"{s}: {a}%" for s, a in zip(all_species, all_abundances) if s]
            )

            all_checks_passed = row.get("all_checks_passed", "False") == "True"
            all_checks_display = "✓" if all_checks_passed else "❌"
            all_checks_color = "color: green;" if all_checks_passed else "color: red;"

            html_fragment += f"""
                    <tr>
                        <td>{sample_id}</td>
                        <td>{top_species}</td>
                        <td>{top_ani}</td>
                        <td>{num_genomes}</td>
                        <td>{species_breakdown}</td>
                        <td style="{all_checks_color}">{all_checks_display}</td>
                    </tr>
            """

        html_fragment += """
                </tbody>
            </table>
        </div>
        """
        return html_fragment
