import math
import numpy as np
from tabulate import tabulate
import pandas as pd
import matplotlib.pyplot as plt
import os
from sensitivity_analysis import *

#### Define the trade-off criteria and their weights ####

# Criteria weights
crit_weights = {"Sustainability": 0.25, "Cost": 0.3, "Performance": 0.2, "Risk": 0.15, "Transportability": 0.1}

# KPI weights
kpi_sustainability = {"TSFC": 0.6, "life-cycle": 0.4}
kpi_cost = {"development": 0.2, "acquisition": 0.4, "operational": 0.4}
kpi_performance = {"payload": 0.5, "stab-control": 0.5}
kpi_risk = {"reliability": 0.5, "certification": 0.2, "safety": 0.3}
kpi_transportability = {"ease": 0.45, "accessibility": 0.55}



#### Results of the KPI calculations ####

results_sustainability = {
    "options": [1, 2, 3, 4, 5],
    "TSFC": [0.4, 0.7, 0.5, 0.1, 0.9],                          # TODO: replace with actual values
    "life-cycle": [0.1, 0.3, 0.5, 0.7, 0.3]         # TODO: replace with actual values
}

results_cost = {
    "options": [1, 2, 3, 4, 5],
    "development": [0.1, 0.3, 0.5, 0.7, 0.9],                   # TODO: replace with actual values
    "acquisition": [0.9, 0.7, 0.5, 0.3, 0.1],                   # TODO: replace with actual values
    "operational": [0.5, 0.6, 0.7, 0.8, 0.9]                    # TODO: replace with actual values
}

results_performance = {
    "options": [1, 2, 3, 4, 5],                                 
    "payload": [0.3, 0.5, 0.7, 0.9, 0.6],                       # TODO: replace with actual values
    "stab-control": [0.9, 0.7, 0.5, 0.3, 0.1]                   # TODO: replace with actual values
}

results_risk = {
    "options": [1, 2, 3, 4, 5],                                 
    "reliability": [0.7, 0.5, 0.3, 0.9, 0.1],                   # TODO: replace with actual values
    "certification": [0.1, 0.3, 0.5, 0.7, 0.9],                 # TODO: replace with actual values
    "safety": [0.9, 0.7, 0.5, 0.3, 0.1]                         # TODO: replace with actual values
}

results_transportability = {
    "options": [1, 2, 3, 4, 5],
    "ease": [0.5, 0.6, 0.7, 0.8, 0.9],                          # TODO: replace with actual values
    "accessibility": [0.9, 0.7, 0.5, 0.3, 0.5]                  # TODO: replace with actual values
}

#### Calculate the weighted scores for each option ####
def calculate_weighted_scores(results, kpi_weights):
    scores = []
    for i in range(len(results["options"])):
        score = 0
        for kpi, weight in kpi_weights.items():
            score += results[kpi][i] * weight
        scores.append(score)
    return scores

def calculate_weighted_scores_from_kpi(kpi_results, kpi_weights):
    scores = []
    num_options = len(next(iter(kpi_results.values())))  # Infer the number of options from the first KPI
    for i in range(num_options):
        score = 0
        for kpi, weight in kpi_weights.items():
            score += kpi_results[kpi][i] * weight
        scores.append(score)
    return scores

def calculate_trade_off_scores(current_crit_weights):
    # Calculate the weighted scores for each option
    scores_sustainability = calculate_weighted_scores(results_sustainability, kpi_sustainability)
    scores_cost = calculate_weighted_scores(results_cost, kpi_cost)
    scores_performance = calculate_weighted_scores(results_performance, kpi_performance)
    scores_risk = calculate_weighted_scores(results_risk, kpi_risk)
    scores_transportability = calculate_weighted_scores(results_transportability, kpi_transportability)

    # Combine the scores using the criteria weights
    trade_off_scores_list = []
    for i in range(len(results_sustainability["options"])):
        score = (scores_sustainability[i] * current_crit_weights["Sustainability"] +
                 scores_cost[i] * current_crit_weights["Cost"] +
                 scores_performance[i] * current_crit_weights["Performance"] +
                 scores_risk[i] * current_crit_weights["Risk"] +
                 scores_transportability[i] * current_crit_weights["Transportability"])
        trade_off_scores_list.append(score)

    return trade_off_scores_list



#### Main function to run the trade-off analysis ####
if __name__ == "__main__":
    trade_off_scores = calculate_trade_off_scores(crit_weights)

    # Generate separate tables for each criterion and their KPIs
    for criterion, (results, kpi_weights) in zip(
        crit_weights.keys(),
        zip(
            [results_sustainability, results_cost, results_performance, results_risk, results_transportability],
            [kpi_sustainability, kpi_cost, kpi_performance, kpi_risk, kpi_transportability],
        ),
    ):
        kpi_table_data = []
        kpi_headers = ["Option"] + list(kpi_weights.keys())

        for i, option in enumerate(results["options"]):
            row = [option] + [results[kpi][i] * weight for kpi, weight in kpi_weights.items()]
            kpi_table_data.append(row)

        print(f"\n{criterion} Breakdown:")
        print(tabulate(kpi_table_data, headers=kpi_headers, floatfmt=".2f", tablefmt="grid"))

    # Prepare data for the final trade-off table
    trade_off_table_data = []
    trade_off_headers = ["Option"] + list(crit_weights.keys()) + ["Final Score"]

    for i, option in enumerate(results_sustainability['options']):
        row = [
            option,
            calculate_weighted_scores(results_sustainability, kpi_sustainability)[i],
            calculate_weighted_scores(results_cost, kpi_cost)[i],
            calculate_weighted_scores(results_performance, kpi_performance)[i],
            calculate_weighted_scores(results_risk, kpi_risk)[i],
            calculate_weighted_scores(results_transportability, kpi_transportability)[i],
            trade_off_scores[i]
        ]
        trade_off_table_data.append(row)

    print("\nFinal Trade-Off Table:")
    print(tabulate(trade_off_table_data, headers=trade_off_headers, floatfmt=".2f", tablefmt="grid"))

    # Perform sensitivity analysis
    print("\nPerforming Sensitivity Analysis...")
    sensitivity_analysis_results = perform_sensitivity_analysis(crit_weights, variation_percentage=0.5)

    for criterion, results in sensitivity_analysis_results.items():
        print(f"\nSensitivity for varying {criterion}:")
        print(f"  Increased Weights: {results['increased_weights']}")
        print(f"  New Scores with increased weight: {[round(x,4) for x in results['increased_scores']]}")
        print(f"  Winner with increased weight: Option {results['winner_increase']}")
        print(f"  Decreased Weights: {results['decreased_weights']}")
        print(f"  New Scores with decreased weight: {[round(x,4) for x in results['decreased_scores']]}")
        print(f"  Winner with decreased weight: Option {results['winner_decrease']}")

    # Generate graphs for sensitivity analysis
    plot_sensitivity_analysis(sensitivity_analysis_results)
    plot_combined_sensitivity_analysis(sensitivity_analysis_results)
    print("\nGraphs for sensitivity analysis have been saved.")

    # Perform KPI sensitivity analysis for each criterion
    for criterion, (results, kpi_weights) in zip(
        crit_weights.keys(),
        zip(
            [results_sustainability, results_cost, results_performance, results_risk, results_transportability],
            [kpi_sustainability, kpi_cost, kpi_performance, kpi_risk, kpi_transportability],
        ),
    ):
        print(f"\nPerforming KPI Sensitivity Analysis for {criterion}...")
        kpi_sensitivity_results = perform_kpi_sensitivity_analysis(kpi_weights, results, variation_percentage=0.25)

        # Plot the results for KPI sensitivity analysis
        plot_kpi_sensitivity_analysis(kpi_sensitivity_results, criterion, kpi_weights, results)
        print(f"KPI Sensitivity Analysis for {criterion} completed.")