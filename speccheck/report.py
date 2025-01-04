

import matplotlib.pyplot as plt
import pandas as pd

def plot_charts(csv_file):
    # Load the CSV file into a DataFrame
    df = pd.read_csv(csv_file)

    # Plotting functions
    def plot_mash_distance():
        plt.figure(figsize=(10, 6))
        plt.plot(df['Speciator.Sample_id'], df['Speciator.mashDistance'], marker='o')
        plt.title('Mash Distance per Sample')
        plt.xlabel('Sample ID')
        plt.ylabel('Mash Distance')
        plt.grid(True)
        plt.show()

    def plot_gc_content():
        plt.figure(figsize=(10, 6))
        df.boxplot(column='Quast.GC (%)', by='Speciator.Sample_id', grid=False)
        plt.title('GC Content per Sample')
        plt.suptitle('')  # Suppress the automatic title to avoid redundancy
        plt.xlabel('Sample ID')
        plt.ylabel('GC Content (%)')
        plt.xticks(rotation=90)
        plt.show()

    def plot_contig_lengths():
        plt.figure(figsize=(10, 6))
        plt.plot(df['Speciator.Sample_id'], df['Quast.Total length'], marker='o', color='r')
        plt.title('Total Contig Length per Sample')
        plt.xlabel('Sample ID')
        plt.ylabel('Total Contig Length')
        plt.grid(True)
        plt.show()

    # Set the style for the plots
    plt.style.use('ggplot')

    # Call plotting functions
    plot_mash_distance()
    plot_gc_content()
    plot_contig_lengths()