import plotly.express as px
import plotly.offline as pyo


class Plot_Checkm:
    def __init__(self, df):
        self.df = df

    def plot(self):
        # Create a scatter plot for Contamination vs Completeness with violin plots
        html_fragment = "<h2>CheckM Plots</h2>"
        
        # Add a short description for CheckM
        html_fragment += """
        <p>CheckM is a tool used to assess the quality of genome bins by evaluating their completeness and contamination. 
        It provides insights into the reliability of genome assemblies.</p>
        """
        
        # Add a summary of the analysis
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
        
        # Create the scatter plot
        fig = px.scatter(
            self.df,
            x="Completeness",
            y="Contamination",
            color="species",
            marginal_x="violin",
            marginal_y="violin",
            title="Scatter Plot of Contamination vs Completeness by Species",
            hover_data=[self.df.index]
        )
        fig.update_layout(
            hovermode="closest",
            xaxis_title="Completeness (%)",
            yaxis_title="Contamination (%)",
            legend_title="Species"
        )
        
        # Check if there is only one unique species
        if self.df["species"].nunique() == 1:
            fig.update_layout(showlegend=False)  # Hide legend if only one species
        
        html_fragment += pyo.plot(fig, include_plotlyjs=False, output_type="div")

        return html_fragment