import pandas as pd
import networkx as nx
from dowhy import gcm
from dowhy.utils import bar_plot
import matplotlib.pyplot as plt
from scipy.stats import halfnorm
import numpy as np
import io
import base64
import seaborn as sns
import json
import argparse

class CausalImpactAnalyzer:
    def __init__(self, 
                 sample_frac = 0.2, 
                 num_bootstrap_resamples = 2, 
                 discover_distributions = False):
        """
        Initialize the CausalImpactAnalyzer.

        Args:
        sample_frac (float): Fraction of the data to sample for analysis. Default is 0.2.
        num_bootstrap_resamples (int): Number of bootstrap resamples to use for confidence interval estimation. Default is 2.
        discover_distributions (bool): Whether to automatically discover causal mechanisms from the data. Default is False.
        """
        self.sample_frac = sample_frac
        self.num_bootstrap_resamples = num_bootstrap_resamples
        self.discover_distributions = discover_distributions

    def identify_attributions(self, normal_data, outlier_data, causal_graph, target_node):
        """
        Analyze the causal impact of outlier data compared to normal data on a target node.

        This function uses a Structural Causal Model to estimate the causal effects
        of changes in the distribution of data on a specified target node.

        Args:
        normal_data (pd.DataFrame): DataFrame containing the normal (baseline) data.
        outlier_data (pd.DataFrame): DataFrame containing the outlier (treatment) data.
        causal_graph (nx.DiGraph): A directed graph representing the causal relationships.
        target_node (str): The name of the node for which to analyze the causal impact.

        Returns:
        tuple: A tuple containing:
            - median_attribs (dict): Median attribution scores for each node.
            - uncertainty_attribs (dict): Uncertainty intervals for each node.
        """

        # Create a Structural Causal Model from the causal graph
        causal_model = gcm.StructuralCausalModel(causal_graph)

        # Set causal mechanisms for each node in the graph
        if not self.discover_distributions:
            for node in causal_graph.nodes:
                if len(list(causal_graph.predecessors(node))) > 0:
                # For nodes with predecessors, use a linear regressor
                    causal_model.set_causal_mechanism(node, gcm.AdditiveNoiseModel(gcm.ml.create_linear_regressor()))
                else:
                    # For root nodes, use a half-normal distribution
                    causal_model.set_causal_mechanism(node, gcm.ScipyDistribution(halfnorm))
        else: 
            gcm.auto.assign_causal_mechanisms(causal_model, normal_data)

        # Compute confidence intervals for the causal impact
        median_attribs, uncertainty_attribs = gcm.confidence_intervals(
            lambda : gcm.distribution_change(causal_model,
                                            normal_data.sample(frac=self.sample_frac),
                                            outlier_data.sample(frac=self.sample_frac),
                                            target_node,
                                            difference_estimation_func=lambda x, y: np.mean(y) - np.mean(x)),
                                            num_bootstrap_resamples = self.num_bootstrap_resamples)
        return median_attribs, uncertainty_attribs

    def load_and_identify_attributions(self, normal_data_path, outlier_data_path, causal_graph_path, target_node_path):
        """
        Load data from given file paths and analyze the causal impact on a target node.

        This function reads the normal data, outlier data, and causal graph from the provided file paths,
        and then analyzes the causal impact of the outlier data compared to the normal data on a target node.

        Args:
        normal_data_path (str): Path to the CSV file containing the normal (baseline) data.
        outlier_data_path (str): Path to the CSV file containing the outlier (treatment) data.
        causal_graph_path (str): Path to the JSON file containing the causal graph.
        target_node_path (str): Path to the text file containing the name of the target node.

        Returns:
        tuple: A tuple containing:
            - median_attribs (dict): Median attribution scores for each node.
            - uncertainty_attribs (dict): Uncertainty intervals for each node.
        """
        normal_data = pd.read_csv(normal_data_path)
        outlier_data = pd.read_csv(outlier_data_path)
        with open(causal_graph_path, 'r') as f:
            causal_graph = nx.node_link_graph(json.load(f))
        with open(target_node_path, 'r') as f:
            target_node = f.read().strip()

        return self.identify_attributions(normal_data, outlier_data, causal_graph, target_node)
    
    def plot_attributions(self, median_attribs, uncertainty_attribs, filepath = "attribution_plot.png"):
        """
        Plot the causal impact of the outlier data compared to the normal data on a target node.
        """
        # write to given file
        bar_plot(median_attribs, uncertainty_attribs, filename = filepath)
        
        # load from file and return as bytes
        with open(filepath, 'rb') as f:
            plot_bytes = f.read()
        return plot_bytes
    

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

def main():
    parser = argparse.ArgumentParser(description='Analyze causal impact using CausalImpactAnalyzer')
    parser.add_argument('normal_data_path', type=str, help='Path to the CSV file containing normal data')
    parser.add_argument('outlier_data_path', type=str, help='Path to the CSV file containing outlier data')
    parser.add_argument('causal_graph_path', type=str, help='Path to the JSON file containing the causal graph')
    parser.add_argument('target_node_path', type=str, help='Path to the text file containing the target node')
    parser.add_argument('--sample_frac', type=float, default=0.2, help='Fraction of data to sample (default: 0.2)')
    parser.add_argument('--num_bootstrap_resamples', type=int, default=2, help='Number of bootstrap resamples (default: 2)')
    parser.add_argument('--discover_distributions', action='store_true', help='Automatically discover causal mechanisms')
    parser.add_argument('--output_plot', type=str, default='attribution_plot.png', help='Path to save the attribution plot (default: attribution_plot.png)')
    parser.add_argument('--output_json', type=str, default='attributions.json', help='Path to save the attributions and uncertainty as JSON (default: attributions.json)')

    args = parser.parse_args()

    analyzer = CausalImpactAnalyzer(
        sample_frac=args.sample_frac,
        num_bootstrap_resamples=args.num_bootstrap_resamples,
        discover_distributions=args.discover_distributions
    )

    median_attribs, uncertainty_attribs = analyzer.load_and_identify_attributions(
        args.normal_data_path,
        args.outlier_data_path,
        args.causal_graph_path,
        args.target_node_path
    )

    # Plot the attributions and save to the specified file without displaying
    plt.ioff()  # Turn off interactive mode
    analyzer.plot_attributions(median_attribs, uncertainty_attribs, filepath=args.output_plot)
    plt.close()  # Close the plot to free up memory
    print(f"Attribution plot saved to {args.output_plot}")

    # Save attributions and uncertainty to JSON
    attributions_data = {
        "median_attributions": median_attribs,
        "uncertainty_attributions": uncertainty_attribs
    }
    with open(args.output_json, 'w') as f:
        json.dump(attributions_data, f, cls=NumpyEncoder, indent=2, default=lambda x: x.tolist() if isinstance(x, np.ndarray) else x)
    print(f"Attributions and uncertainty saved to {args.output_json}")

if __name__ == "__main__":
    main()
    # Example usage:
    # Run the script from the command line with the following arguments:
    # conda activate py-causal
    # python causal_analyzer.py dummy_data/rca_microservice_architecture_latencies.csv dummy_data/rca_microservice_architecture_anomaly_1000.csv dummy_data/causal_graph.json dummy_data/target_node.txt

    # You can also add optional arguments:
    # --sample_frac 0.3
    # --num_bootstrap_resamples 5
    # --discover_distributions
    # --output_plot my_attribution_plot.png
    # --output_json my_attributions.json

    # Full example with optional arguments:
    # python causal_analyzer.py dummy_data/rca_microservice_architecture_latencies.csv dummy_data/rca_microservice_architecture_anomaly_1000.csv dummy_data/causal_graph.json dummy_data/target_node.txt --sample_frac 0.3 --num_bootstrap_resamples 5 --discover_distributions --output_plot my_attribution_plot.png --output_json my_attributions.json

