import json
import numpy as np
import pandas as pd
import networkx as nx
from dowhy import gcm
from scipy import stats
from scipy.stats import truncexpon, halfnorm, bernoulli
from typing import Dict, List, Tuple
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from typing import Dict, Tuple

from causal_analyzer import CausalImpactAnalyzer

#### HELPERS - ANOMALY DETECTION ####
class AnomalyAggregator: 
    def __init__(self, 
                 detection_method: str = 'isolation_forest',
                 contamination: float = 0.1,
                 z_score_threshold: float = 3.0, 
                 metric_names: List[str] = ['rate', 'error_rate', 'duration']):
        """
        Initialize the AnomalyAggregator.

        Args:
            detection_method (str): Method for anomaly detection. Options are 'isolation_forest', 'robust_covariance', or 'z_score'.
            contamination (float): Expected proportion of anomalies (for isolation_forest and robust_covariance methods).
            z_score_threshold (float): Threshold for z-score method.
            metric_names (List[str]): List of metric names to use for anomaly detection. Default is ['rate', 'error_rate', 'duration'].
        """

        self.detection_method = detection_method
        self.contamination = contamination
        self.z_score_threshold = z_score_threshold
        self.metric_names = metric_names
        self.anomaly_detectors = {}
        self.baselines = {}

    def _create_detector(self, service: str) -> object:
        """Create anomaly detector for a service."""
        if self.detection_method == 'isolation_forest':
            return IsolationForest(
                contamination=self.contamination,
                random_state=42
            )
        elif self.detection_method == 'robust_covariance':
            return EllipticEnvelope(
                contamination=self.contamination,
                random_state=42
            )
        else:  # z_score method
            return None

    def fit_detectors(self, training_data: pd.DataFrame):
        """
        Fit anomaly detectors for each service using training data.
        
        Args:
            training_data: DataFrame with columns [timestamp, service, rate, error_rate, error_count, request_count, duration]
        """
        for service in training_data['service'].unique():
            # Get service data
            service_data = training_data[training_data['service'] == service]
            
            # Prepare RED metrics matrix
            X = service_data[self.metric_names].values
            
            if self.detection_method in ['isolation_forest', 'robust_covariance']:
                detector = self._create_detector(service)
                detector.fit(X)
                self.anomaly_detectors[service] = detector
            else:  # z_score method
                self.baselines[service] = {
                    'mean': X.mean(axis=0),
                    'std': X.std(axis=0)
                }

    def calculate_anomaly_scores(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate anomaly scores for each service.
        
        Args:
            data: DataFrame with RED metrics
            
        Returns:
            DataFrame with anomaly scores per service per time_index
        """
        scores = []

        for service in data['service'].unique():
            service_data = data[data['service'] == service]

            if len(service_data) == 0:
                continue

            # Get RED metrics
            X = service_data[self.metric_names].values

            # Get anomaly scores
            return_field_wise = False
            if self.detection_method == 'isolation_forest':
                # Convert to positive scores where higher means more anomalous
                raw_scores = -self.anomaly_detectors[service].score_samples(X)
            elif self.detection_method == 'robust_covariance':
                # Mahalanobis distances
                raw_scores = self.anomaly_detectors[service].mahalanobis(X)
            else:  # z_score method
                z_scores = (X - self.baselines[service]['mean']) / self.baselines[service]['std']
                z_scores_abs = np.abs(z_scores)
                z_scores_dict = {metric: z_scores_abs[:, i] for i, metric in enumerate(self.metric_names)}
                raw_scores = np.max(z_scores_abs, axis=1)  # Use the maximum z-score across metrics
                return_field_wise = True

            # Create score records
            for idx, score in enumerate(raw_scores):
                record = {
                    'time_index': service_data.iloc[idx]['time_index'],
                    'service': service,
                    'anomaly_score': score,
                }
                if return_field_wise:
                    for metric, z_scores in z_scores_dict.items():
                        record[f'z_score__{metric}'] = z_scores[idx]
                scores.append(record)
        return pd.DataFrame(scores)

### ALTERNATIVE 1: AGGREGATE ACROSS METRICS THEN DO ATTRIBUTION 
def analyze_with_aggregated_anomaly_scores(causal_graph, 
                                           normal_data, 
                                           anomalous_data, 
                                           target_node, 
                                           display_results = False):
    def compute_percent_contrib(median_attribs):
        attribs_df = pd.DataFrame(median_attribs).abs()
        total_attribs_value = attribs_df['median_attribs'].sum()
        attribs_df['percent_contrib'] = attribs_df['median_attribs'] / total_attribs_value*100
        return attribs_df[['percent_contrib']]

    # Initialize the AnomalyAggregator with z_score method
    aggregator = AnomalyAggregator(detection_method='z_score')

    # Fit the detectors using the normal data
    aggregator.fit_detectors(normal_data)

    # Calculate anomaly scores for the anomalous data
    normal_data_ascores  = aggregator.calculate_anomaly_scores(normal_data).pivot(index='time_index', columns='service', values='anomaly_score')
    anomaly_data_ascores = aggregator.calculate_anomaly_scores(anomalous_data).pivot(index='time_index', columns='service', values='anomaly_score')

    # Create an instance of the CausalImpactAnalyzer
    analyzer = CausalImpactAnalyzer(discover_distributions=True, num_bootstrap_resamples=4)

    # Load data and identify attributions
    median_attribs, uncertainty_attribs = analyzer.identify_attributions(
        normal_data_ascores,
        anomaly_data_ascores, 
        causal_graph, 
        target_node
    )

    # Plot the attributions
    if display_results:
        _ = analyzer.plot_attributions(median_attribs, uncertainty_attribs)
    return {'median_attribs':median_attribs, 'uncertainty_attribs':uncertainty_attribs}

### ALTERNATIVE 2: RUN ANALYSIS PER METRIC THEN AGGREGATE ATTRIBUTIONS 
def analyze_per_metric(causal_graph, 
                       normal_data, 
                       anomalous_data, 
                       target_node, 
                       contribution_perc_floor = 20, 
                       display_results = False):
    def compute_percent_contrib(results, metric):
        attribs_df = pd.DataFrame(results[metric])[['median_attribs']].abs()
        total_attribs_value = attribs_df['median_attribs'].sum()
        attribs_df['percent_contrib'] = attribs_df['median_attribs'] / total_attribs_value*100
        return attribs_df[['percent_contrib']]

    # Filter metrics to ones that are anomalous 
    # (note: I put this lil hack in cause needa figure out how to account for non-anomalous metrics, 
    # here rate - which has no discernible difference with norm)

    # Initialize the AnomalyAggregator with z_score 
    aggregator = AnomalyAggregator(detection_method='z_score')

    # Fit the detectors using the normal data
    aggregator.fit_detectors(normal_data)

    # Calculate anomaly scores for anomalous data
    anomaly_data_ascores = aggregator.calculate_anomaly_scores(anomalous_data)

    # determine which metrics are anomalous
    z_thresh = 2
    z_score_columns = [col for col in anomaly_data_ascores.columns if col.startswith('z_score_')]
    agg_anomaly_ascores = anomaly_data_ascores.groupby('service')[z_score_columns].mean()
    anomalous_service_metrics_df = agg_anomaly_ascores > z_thresh

    # get list of anomalous metrics
    anomalous_metrics_series = anomalous_service_metrics_df.any()
    anomalous_metrics = anomalous_metrics_series[anomalous_metrics_series].index.tolist()
    anomalous_metrics = [m.replace('z_score__', '') for m in anomalous_metrics]    

    # Apply analyzer individually to each metric
    results = {}
    for metric in anomalous_metrics:
        analyzer = CausalImpactAnalyzer(discover_distributions=True, 
                                        num_bootstrap_resamples=2)
        median_attribs, uncertainty_attribs = analyzer.identify_attributions(
            normal_data.pivot(index='time_index', columns='service', values=metric),
            anomalous_data.pivot(index='time_index', columns='service', values=metric), 
            causal_graph, 
            target_node
        )
        results[metric] = {
            'median_attribs': median_attribs,
            'uncertainty_attribs': uncertainty_attribs
        }

    # convert to percent contributions and filter by contribution_perc_floor
    for metric in anomalous_metrics:
        if display_results:
            print(f"Plotting attributions for {metric}")
            _ = analyzer.plot_attributions(results[metric]['median_attribs'], results[metric]['uncertainty_attribs'])
        contributions = compute_percent_contrib(results, metric)
        significant_contributions = contributions[contributions['percent_contrib'] > contribution_perc_floor].to_dict()
        results[metric].update(significant_contributions)
        if display_results:
            print(f"Percent contributions for {metric}: {significant_contributions}")

    return {'per_metric_attributions':results}


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze causal impact using CausalImpactAnalyzer')
    parser.add_argument('normal_data_path', type=str, help='Path to the CSV file containing normal data')
    parser.add_argument('outlier_data_path', type=str, help='Path to the CSV file containing outlier data')
    parser.add_argument('causal_graph_path', type=str, help='Path to the JSON file containing the causal graph')
    parser.add_argument('target_node_path', type=str, help='Path to the text file containing the target node')
    parser.add_argument('--analysis_type', type=str, choices=['a1', 'a4'], default='a4',
                        help='Type of analysis to perform: aggregated or per_metric')
    parser.add_argument('--output_json', type=str, default='attributions.json',
                        help='Path to save the attributions as JSON (default: attributions.json)')

    args = parser.parse_args()

    # Load data
    normal_data = pd.read_csv(args.normal_data_path)
    outlier_data = pd.read_csv(args.outlier_data_path)
    with open(args.causal_graph_path, 'r') as f:
        causal_graph = nx.node_link_graph(json.load(f))
    with open(args.target_node_path, 'r') as f:
        target_node = f.read().strip()

    # Perform analysis
    if args.analysis_type == 'a1':
        results = analyze_with_aggregated_anomaly_scores(causal_graph, normal_data, outlier_data, target_node)
    elif args.analysis_type == 'a4':
        results = analyze_per_metric(causal_graph, normal_data, outlier_data, target_node)

    # Save results to JSON
    with open(args.output_json, 'w') as f:
        json.dump(results, f, cls=NumpyEncoder, indent=2)
    print(f"Results saved to {args.output_json}")

if __name__ == "__main__":
    main()
    # Example usage:
    # Run the script from the command line with the following arguments:
    # conda activate py-causal
    # python red_causal_analyzer.py simulated_multimetric_data/normal_data.csv  simulated_multimetric_data/anomalous_data.csv simulated_multimetric_data/causal_graph.json simulated_multimetric_data/target_node.txt