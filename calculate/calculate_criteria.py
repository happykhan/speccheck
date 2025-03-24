#!/usr/bin/env python3
"""
This script processes assembly statistics and generates plots for specified species.

Functions:
    get_file(url, workdir, prefix):

    make_stat_dict(the_list):
        Creates a dictionary for statistical metrics.

    main(args):
        Main function to process assembly stats and generate plots based on the provided arguments.

Arguments:
    --workdir (str): Working directory where files will be saved and processed.
    --species (list of str): List of species to include in the analysis.
    --min_genome_count (int): Minimum number of genomes per species to include in the analysis.
    --metrics_list (list of str): List of metrics to include in the analysis.

Usage:
    python calculate_criteria.py --workdir <working_directory> --species
        <species_list> --min_genome_count <min_genome_count> --metrics_list <metrics_list>
"""
import os
import argparse
import pandas as pd
from scipy.stats import normaltest
import numpy as np
import matplotlib.pyplot as plt
from refseq import get_metrics
from scipy.stats.mstats import winsorize
import seaborn as sns
import statsmodels.api as sm
from scipy.stats import ks_2samp, wasserstein_distance
from sklearn.metrics import silhouette_score
from sklearn.cluster import DBSCAN
import logging
from sklearn.neighbors import LocalOutlierFactor
from prepare import filter_assembly_data, prepare

logging.basicConfig(level=logging.INFO)

def basic_stats(metric, metric_data):
    metric_summary = {'metric': metric}
    if isinstance(metric_data, pd.Series):
        metric_data = metric_data.dropna()
    _, p = normaltest(metric_data)               
    metric_summary["distribution"] = "normal" if p > 0.05 else "non-normal"
    metric_summary["mean"] = np.mean(metric_data)
    metric_summary["std"] = np.std(metric_data)
    metric_summary["median"] = np.median(metric_data)
    metric_summary["iqr"] = np.percentile(metric_data, 75) - np.percentile(
        metric_data, 25
    )
    metric_summary["min"] = metric_data.min()
    metric_summary["max"] = metric_data.max()    
    if len(metric_data) > 10000:
        metric_data = np.random.choice(metric_data, size=10000, replace=False)
    metric_data = np.array(metric_data)
    lof = LocalOutlierFactor(n_neighbors=100, contamination='auto')  # Adjust contamination for sensitivity
    outlier_scores = lof.fit_predict(metric_data.reshape(-1, 1))  # -1 = Outlier, 1 = Inlier

    # Filter: Keep only inliers
    kde_density_filtered = metric_data[outlier_scores == 1].flatten()
    metric_data = metric_data[outlier_scores == 1]
    if kde_density_filtered.size > 0:
        metric_summary["lof_upper_bound"] = np.percentile(kde_density_filtered, 98)
        metric_summary["lof_lower_bound"] = np.percentile(kde_density_filtered, 2)
        metric_summary["kde_upper_bound"] = np.percentile(kde_density_filtered, 98)
        metric_summary["kde_lower_bound"] = np.percentile(kde_density_filtered, 2)

    if metric_summary.get("kde_upper_bound") is None:
        metric_summary["kde_upper_bound"] = np.max(metric_data)
        metric_summary["kde_lower_bound"] = np.min(metric_data)
    return metric_summary, metric_data



def plot_histogram(metric, sra_values, refseq_values, workdir):
    # Overlayed Histogram and KDE
    plt.figure()
    sns.histplot(
        sra_values,
        bins=50,
        color="blue",
        stat="density",
        kde=True,
        alpha=0.6,
        label="SRA",
    )
    sns.histplot(
        refseq_values,
        bins=50,
        color="red",
        stat="density",
        kde=True,
        alpha=0.6,
        label="RefSeq",
    )
    plt.title(f"Overlayed Histogram and KDE ({metric})")
    plt.xlabel("Value")
    plt.ylabel("Density")
    plt.legend()
    plt.savefig(
        os.path.join(
            workdir, f"{metric}_refseq_histogram_kde.png"
        )
    )
    plt.close('all')

    # Q-Q Plot
    plt.figure()
    sm.qqplot_2samples(sra_values, refseq_values, line="45")
    plt.title(f"Q-Q Plot of SRA vs RefSeq ({metric})")
    plt.xlabel("Quartiles of SRA")
    plt.ylabel("Quartiles of RefSeq")
    plt.savefig(
        os.path.join(workdir, f"{metric}_refseq_qqplot.png")
    )
    plt.close('all')


def get_cluster_stats(metric, this_metric_data, eps, min_samples=5):
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)  # Adjust `eps` for density and `min_samples` for clustering threshold    
    this_metric_data["cluster"] = dbscan.fit_predict(this_metric_data)
    # Step 3: Count the number of points in each cluster
    cluster_counts = this_metric_data["cluster"].value_counts()

    # Step 4: Get the cluster with the maximum count
    max_cluster = cluster_counts.idxmax()  # Cluster label with the most points
    # get cluster with the most 
    largest_cluster_data = this_metric_data[this_metric_data["cluster"] == max_cluster]
    metric_cluster_stats, metric_cluster = basic_stats(metric, largest_cluster_data[metric])
    return metric_cluster_stats, metric_cluster

def plot_comparison(metric, data_1, data_2, workdir):

    # plot histogram comparison of species_data[metric] and metric_data_array
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    sns.histplot(data_1, bins=50, color="green", stat="density", kde=True, alpha=0.6, label="Original", ax=axes[0])
    axes[0].set_title(f"Original Data")
    axes[0].set_xlabel("Value")
    axes[0].set_ylabel("Density")
    axes[0].legend()

    sns.histplot(data_2, bins=50, color="purple", stat="density", kde=True, alpha=0.6, label="Filtered", ax=axes[1])
    axes[1].set_title(f"Filtered Data")
    axes[1].set_xlabel("Value")
    axes[1].set_ylabel("Density")
    axes[1].legend()    
    plt.suptitle(f"Histogram Comparison ({metric})")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(os.path.join(workdir, f"{metric}_comparison_histogram.png"))
    plt.close('all')



def main(args):
    workdir = args.workdir
    species_list = args.species
    min_genome_count = args.min_genome_count
    metrics_list = args.metrics_list
    assembly_stats = prepare(workdir)    
    # Handle species with underscores
    # Rename species according to ^([A-Za-z]+)_?[A-Za-z]*\s([a-z]+) 
    assembly_stats = filter_assembly_data(assembly_stats, min_genome_count, species_list)
    species_list = set(assembly_stats["species_sylph"])
    all_metrics_for_all_species = []
    # Look at refseq first, calibrate contamination and completeness cutoffs
    for species in species_list:
        species_data = assembly_stats[assembly_stats["species_sylph"] == species]
        if len(species_data) < min_genome_count:
            print(f"Skipping {species} due to insufficient genomes.")
            continue        
        refseq_data = get_metrics(species)
        species_dir = os.path.join(workdir, species.replace(" ", "_"))
        os.makedirs(species_dir, exist_ok=True)
        metric_summary = []
        remaining_metrics = []
        for metric in metrics_list:
            refseq_metric_values = refseq_data.get(metric)
            if refseq_metric_values is not None:
                refseq_metric_values = np.array(refseq_metric_values)
                metric_stats, metric_data = basic_stats(metric, species_data[metric])
                metric_data_array = np.array(metric_data)
                plot_comparison(metric, species_data[metric], metric_data_array, species_dir)

                ks_statistic, ks_p_value = ks_2samp(metric_data_array, refseq_metric_values)
                w_distance = wasserstein_distance(metric_data_array, refseq_metric_values)
                refseq_metric_stats, refseq_filtered_values = basic_stats(metric, refseq_metric_values)
                plot_comparison(metric + '_refseq', refseq_metric_values, refseq_filtered_values, species_dir)
                refseq_metric_stats.pop("metric", None)
                refseq_metric_stats = {f"refseq_{k}": v for k, v in refseq_metric_stats.items()}
                metric_stats.update(refseq_metric_stats)
                metric_stats["KS_statistic"] = ks_statistic
                metric_stats["KS_p_value"] = ks_p_value
                metric_stats["Wasserstein_Distance"] = w_distance
                # Adjusted ranges
                if metric == 'GC_Content':
                    metric_stats["upper_bound"] = metric_stats["refseq_max"]
                    metric_stats["lower_bound"] = metric_stats["refseq_min"]
                    if metric_stats["upper_bound"] == metric_stats["lower_bound"]:
                        metric_stats["upper_bound"] += 0.01
                        metric_stats["lower_bound"] -= 0.01
                else:
                    metric_stats["upper_bound"] = round(max(metric_stats['kde_upper_bound'], metric_stats["refseq_kde_upper_bound"]), 2)
                    metric_stats["lower_bound"] = round(min(metric_stats["kde_lower_bound"], metric_stats["refseq_kde_lower_bound"]), 2)
                    # metric_stats["lower_bound"] = max(0, metric_stats["lower_bound"])
                # Overlayed Histogram and KDE
                metric_data_win = winsorize(metric_data, limits=[0.0001, 0.0001])
                plot_histogram(metric, metric_data_win, refseq_metric_values, species_dir)
                metric_summary.append(metric_stats)
                metric_stats['species'] = species
                metric_stats['count'] = len(species_data)
                all_metrics_for_all_species.append(metric_stats)
            else:
                remaining_metrics.append(metric)
        # Plot Total_Coding_Sequences vs Genome_Size
        plt.figure()
        sns.scatterplot(
            y="Total_Coding_Sequences",
            x="Genome_Size",
            data=species_data,
            hue="Completeness_Specific",
            palette="viridis",
        )
        plt.savefig(os.path.join(species_dir, f"CDS_vs_Genome_Size.png"))
        plt.close('all')

        genome_size_lower = float([x for x in metric_summary if x['metric'] == 'Genome_Size'][0]['lower_bound'])
        genome_size_upper = float([x for x in metric_summary if x['metric'] == 'Genome_Size'][0]['upper_bound'])
        gc_content_lower = float([x for x in metric_summary if x['metric'] == 'GC_Content'][0]['lower_bound'])
        gc_content_upper = float([x for x in metric_summary if x['metric'] == 'GC_Content'][0]['upper_bound'])

        lof = LocalOutlierFactor(n_neighbors=20, contamination='auto')  # Adjust contamination for sensitivity
        X_with_outliers = species_data[['number', 'N50', 'longest', 'Genome_Size']]

        # Plotting
        y_pred = lof.fit_predict(X_with_outliers)

        # -1 indicates outliers, 1 indicates inliers
        X_with_outliers['Outlier'] = ['Outlier' if x == -1 else 'Inlier' for x in y_pred]

        # Pair plot
        # sns.pairplot(X_with_outliers, hue='Outlier', palette={'Inlier': 'blue', 'Outlier': 'red'})
        # plt.suptitle('Pair Plot of Species Data with LOF Outliers', y=1.02)
        # plt.show()

        for metric in remaining_metrics:
            # filter species_data with Genome_Size upper_bound and lower_bound
            all_metric_data = species_data[
                (species_data["Genome_Size"] >= genome_size_lower) &
                (species_data["Genome_Size"] <= genome_size_upper) &
                (species_data["GC_Content"] >= gc_content_lower) &
                (species_data["GC_Content"] <= gc_content_upper) 
            ]
            # Plot Total_Coding_Sequences vs Genome_Size
            plt.figure()
            sns.scatterplot(
                x="Genome_Size",
                y="Total_Coding_Sequences",
                data=all_metric_data,
                hue="Completeness_Specific",
                palette="viridis",
            )
            plt.savefig(os.path.join(species_dir, f"filt_CDS_vs_Genome_Size.png"))
            plt.close('all')            

            this_metric_data = species_data[
                (species_data["Genome_Size"] >= genome_size_lower) &
                (species_data["Genome_Size"] <= genome_size_upper) &
                (species_data["GC_Content"] >= gc_content_lower) &
                (species_data["GC_Content"] <= gc_content_upper)
            ][[metric]]
            this_metric_data = species_data[[metric]]
            # EPS for DBSCAN clustering
            # should a fraction of the range of the metric
            SUBSAMPLE_ITERATIONS = 10
            # randomly subsample down to 50,000 points if more than that
            cluster_stats_list = [ ]
            db_scan_output_dir = os.path.join(species_dir, "dbscan")
            os.makedirs(db_scan_output_dir, exist_ok=True)
            if len(this_metric_data) > 1000:
                this_metric_data_sub = this_metric_data.sample(n=1000, random_state=None)
            else:
                this_metric_data_sub = this_metric_data
            if metric == 'number':
                eps_values = np.linspace(1, 100, 20)  # Try a range of eps values
            elif metric == 'longest':
                eps_values = np.linspace(100, 20000, 20)  # Try a range of eps values
            elif metric == 'N50':
                eps_values = np.linspace(100, 5000, 20)
            else:
                eps_values = np.linspace(1, 1000, 20)
            best_eps, best_score = 0, -1
            
            for eps in eps_values:
                dbscan = DBSCAN(eps=eps, min_samples=4).fit(this_metric_data_sub)
                labels = dbscan.labels_
                
                # Ignore cases where all points are noise
                if len(set(labels)) > 1:
                    score = silhouette_score(this_metric_data_sub, labels)
                    if score > best_score:
                        best_eps, best_score = eps, score

            print(f"Optimal eps {metric} - {species}: {best_eps}")
            if best_eps == 0:
                if metric in ["N50"]:
                    best_eps = 1000
                elif metric in ['longest']:
                    best_eps = 10000
                else:
                    best_eps = 50

            if len(this_metric_data) > 10000:
                for i in range(SUBSAMPLE_ITERATIONS):
                    this_metric_data_sub = this_metric_data.sample(n=10000, random_state=None)
                    cluster_stats, cluster = get_cluster_stats(metric, this_metric_data_sub, best_eps)
                    cluster_stats.pop("metric", None)
                    cluster_stats.pop("distribution", None)                    
                    cluster_stats_list.append(cluster_stats)
                    if i % 2 == 0:
                        plot_dbscan(metric, this_metric_data_sub, db_scan_output_dir, f"subsample_{i}")

            else:
                cluster_stats, cluster = get_cluster_stats(metric, this_metric_data, best_eps)
                cluster_stats.pop("metric", None)
                cluster_stats.pop("distribution", None)
                cluster_stats_list.append(cluster_stats)
                plot_dbscan(metric, this_metric_data, db_scan_output_dir, "full")
            cluster_stats_df = pd.DataFrame(cluster_stats_list)
            # average the cluster stats
            cluster_stats_summary = cluster_stats_df.mean().to_dict()
            cluster_stats_summary["metric"] = metric
            cluster_stats_summary["distribution"] = "clustered"

            # plot original and filtered distributions 
            metricdict, filt_data = basic_stats(metric, this_metric_data[metric])
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            plot_comparison(metric, this_metric_data[metric], filt_data, species_dir)

            # Adjusted ranges
            # upper bound cannot be higher than max
            cluster_stats_summary["upper_bound"] = round(min(float(cluster_stats_summary["max"]), float(cluster_stats_summary["kde_upper_bound"])), 2)
            # lower bound cannot be lower than min
            cluster_stats_summary["lower_bound"] = round(max(0, float(cluster_stats_summary["min"]), float(cluster_stats_summary["kde_lower_bound"])), 2)
            metric_summary.append(cluster_stats_summary)
            cluster_stats_summary['species'] = species
            cluster_stats_summary['count'] = len(species_data)
            all_metrics_for_all_species.append(cluster_stats_summary)
        # write the summary to a file
        # Convert the list of dictionaries to a DataFrame and save it as a CSV file
        summary_df = pd.DataFrame(metric_summary)
        summary_df.to_csv(os.path.join(species_dir, "summary.csv"), index=False)
        # Create a summary DataFrame with selected columns
        selected_columns = ["metric", "median", "iqr", "min", "max", "upper_bound", "lower_bound"]
        selected_summary_df = summary_df[selected_columns]
        selected_summary_df.to_csv(os.path.join(species_dir, "selected_summary.csv"), index=False)
    # Save all metrics for all species
    all_metrics_df = pd.DataFrame(all_metrics_for_all_species)
    all_metrics_df.to_csv(os.path.join(workdir, "all_metrics.csv"), index=False)
    selected_columns = ["species", "metric","count", "median", "iqr", "min", "max", "upper_bound", "lower_bound"]
    selected_summary_df = all_metrics_df[selected_columns]
    selected_summary_df.to_csv(os.path.join(workdir, "all_metrics_summary.csv"), index=False)
    for metric in metrics_list:
        # Prepare box plot data
        box_data = []
        labels = []
        extra_lines = [] 
        for species, group in all_metrics_df.groupby("species"):
            metric_data = group[group["metric"] == metric]
            if not metric_data.empty:
                median = metric_data["median"].values[0]
                iqr = metric_data["iqr"].values[0]
                q1 = median - (iqr / 2)  # 25th percentile
                q3 = median + (iqr / 2)  # 75th percentile
                whisker_low = metric_data["min"].values[0]  # Lower whisker
                whisker_high = metric_data["max"].values[0]  # Upper whisker
                # Store five-number summary
                box_data.append([whisker_low, q1, median, q3, whisker_high])
                labels.append(species)
                extra_lines.append((metric_data['lower_bound'], metric_data['upper_bound']))
                

        # Plot box plots for all groups
        plt.figure(figsize=(7, 9))
        plt.boxplot(box_data, vert=True, patch_artist=True, labels=labels)
        # Add extra lines per species
        for i, (lower_bounds, upper_bounds) in enumerate(extra_lines, start=1):
            plt.hlines(y=lower_bounds, xmin=i-0.3, xmax=i+0.3, colors='red', linestyles='dashed', label="Upper bounds" if i == 1 else "")
            plt.hlines(y=upper_bounds, xmin=i-0.3, xmax=i+0.3, colors='blue', linestyles='dashed', label="Lower bounds" if i == 1 else "")

        plt.ylabel("Value")
        plt.title(f"Distribution of cutoffs - {metric}")
        plt.grid(axis="y", linestyle="--", alpha=0.6)
        # Convert x labels to "First letter. Second word" format
        new_labels = [f"{label.split()[0][0]}. {label.split()[1]}" for label in labels]
        plt.xticks(ticks=range(1, len(new_labels) + 1), labels=new_labels, rotation=45)
        plt.savefig(os.path.join(workdir, f"{metric}_boxplot.png"))
        plt.close('all')


def plot_dbscan(metric, data, workdir, suffix):
    plt.figure()
    sns.histplot(data, x=metric, hue="cluster", multiple="stack", palette="tab10", bins=50)
    plt.title(f"Histogram of {metric} colored by DBSCAN clusters")
    plt.xlabel(metric)
    plt.ylabel("Count")
    plt.savefig(os.path.join(workdir, f"{metric}_dbscan_histogram_{suffix}.png"))
    plt.close('all')


if __name__ == "__main__":
    MIN_GENOME_COUNT = 1000  # Minimum number of genomes per species
    METRICS_LIST = [
        "N50",
        "number",
        "longest",
        "GC_Content",
        "Completeness_Specific",
        "Contamination",
        "Total_Coding_Sequences",
        "Genome_Size",
    ]
    SPECIES_LIST = [
        "Salmonella enterica",
        "Escherichia coli",
        "Staphylococcus aureus",
        "Listeria monocytogenes",
        "Campylobacter jejuni",
        "Clostridium difficile",
        "Enterococcus faecalis",
        "Enterococcus faecium",
        "Klebsiella pneumoniae",
        "Acinetobacter baumannii",
        "Pseudomonas aeruginosa",
        "Neisseria gonorrhoeae",
        "Vibrio cholerae",
        "Haemophilus influenzae",
    ]
    SPECIES_LIST = ['Listeria monocytogenes', 'Salmonella enterica', 'Escherichia coli', 'Klesiella pneumoniae']
    parser = argparse.ArgumentParser(
        description="Process assembly stats and generate plots."
    )
    parser.add_argument(
        "--workdir", type=str, default="calculate_workdir", help="Working directory"
    )
    parser.add_argument(
        "--species",
        type=str,
        nargs="+",
        default=SPECIES_LIST,
        help="List of species to include",
    )
    parser.add_argument(
        "--min_genome_count",
        type=int,
        default=MIN_GENOME_COUNT,
        help="Minimum number of genomes per species",
    )
    parser.add_argument(
        "--metrics_list",
        type=str,
        nargs="+",
        default=METRICS_LIST,
        help="List of metrics to include",
    )
    args = parser.parse_args()
    main(args)
