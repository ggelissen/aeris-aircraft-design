import math
import numpy as np
from tabulate import tabulate
import pandas as pd
import matplotlib.pyplot as plt
import os
from tradeoff.sensitivity_analysis import *

#### Define the trade-off criteria and their weights ####

# Criteria weights
crit_weights = {"Sustainability": 0.25, "Cost": 0.3, "Performance": 0.2, "Risk": 0.15, "Transportability": 0.1}

# KPI weights
kpi_sustainability = {"Fuel Consumption": 0.7, "Production and Disposal": 0.3}
kpi_cost = {"Development Cost": 0.2, "Acquisition Cost": 0.4, "Operational Cost": 0.4}
kpi_performance = {"Payload Capacity": 0.5, "Stability and Control": 0.5}
kpi_risk = {"Reliability": 0.4, "Certification Risk": 0.3, "Safety": 0.3}
kpi_transportability = {"Ease of Disassembly": 0.40, "Payload Accessibility": 0.60}



#### Results of the KPI calculations ####

results_sustainability = {
    "options": [1, 2, 3, 4, 5],
    "Fuel Consumption": [3, 4, 5, 1, 1],                         
    "Production and Disposal": [4, 4, 3, 2, 1]
}

results_cost = {
    "options": [1, 2, 3, 4, 5],
    "Development Cost": [4, 4, 4, 2, 1],                  
    "Acquisition Cost": [4, 4, 4, 2, 1],                  
    "Operational Cost": [4, 4, 4, 2, 2]               
}

results_performance = {
    "options": [1, 2, 3, 4, 5],                                 
    "Payload Capacity": [4, 4, 5, 1, 3],                    
    "Stability and Control": [4, 4, 2, 3, 4]             
}

results_risk = {
    "options": [1, 2, 3, 4, 5],                                 
    "Reliability": [3, 3, 1, 4, 4],               
    "Certification Risk": [2, 2, 2, 4, 4],               
    "Safety": [3, 4, 4, 2, 3] 
}                        

results_transportability = {
    "options": [1, 2, 3, 4, 5],
    "Ease of Disassembly": [5, 4, 1, 2, 3],                         
    "Payload Accessibility": [5, 5, 3, 2, 2]          
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

    # Print the winner
    winner_index = np.argmax(trade_off_scores)
    print(f"\nWinner: Option {results_sustainability['options'][winner_index]} with a score of {trade_off_scores[winner_index]:.2f}")

    # Perform sensitivity analysis
    #print("\nPerforming Sensitivity Analysis...")
    sensitivity_analysis_results = perform_sensitivity_analysis(crit_weights, variation_percentage=0.5)

    # for criterion, results in sensitivity_analysis_results.items():
    #     print(f"\nSensitivity for varying {criterion}:")
    #     print(f"  Increased Weights: {results['increased_weights']}")
    #     print(f"  New Scores with increased weight: {[round(x,4) for x in results['increased_scores']]}")
    #     print(f"  Winner with increased weight: Option {results['winner_increase']}")
    #     print(f"  Decreased Weights: {results['decreased_weights']}")
    #     print(f"  New Scores with decreased weight: {[round(x,4) for x in results['decreased_scores']]}")
    #     print(f"  Winner with decreased weight: Option {results['winner_decrease']}")

    # Generate graphs for sensitivity analysis
    plot_sensitivity_analysis(sensitivity_analysis_results)
    plot_combined_sensitivity_analysis(sensitivity_analysis_results)
    # --- Cumulative Boxplot Visualization: Combined Sensitivity Analysis ---
    plot_combined_sensitivity_boxplot(sensitivity_analysis_results)
    # --- Emphasized Cumulative Boxplot Visualization: Combined Sensitivity Analysis ---
    plot_combined_sensitivity_boxplot(sensitivity_analysis_results, variation_percentage=1.0)
    #print("\nGraphs for sensitivity analysis have been saved.")

    # Perform KPI sensitivity analysis for each criterion
    for criterion, (results, kpi_weights) in zip(
        crit_weights.keys(),
        zip(
            [results_sustainability, results_cost, results_performance, results_risk, results_transportability],
            [kpi_sustainability, kpi_cost, kpi_performance, kpi_risk, kpi_transportability],
        ),
    ):
        #print(f"\nPerforming KPI Sensitivity Analysis for {criterion}...")
        kpi_sensitivity_results = perform_kpi_sensitivity_analysis(kpi_weights, results, variation_percentage=0.5)

        # Plot the results for KPI sensitivity analysis
        plot_kpi_sensitivity_analysis(kpi_sensitivity_results, criterion, kpi_weights, results)
        #print(f"KPI Sensitivity Analysis for {criterion} completed.")

    # Perform combined KPI sensitivity analysis for each criterion
    for criterion, (results, kpi_weights) in zip(
        crit_weights.keys(),
        zip(
            [results_sustainability, results_cost, results_performance, results_risk, results_transportability],
            [kpi_sustainability, kpi_cost, kpi_performance, kpi_risk, kpi_transportability],
        ),
    ):
        #print(f"\nGenerating Combined KPI Sensitivity Analysis for {criterion}...")
        kpi_sensitivity_results = perform_kpi_sensitivity_analysis(kpi_weights, results, variation_percentage=0.5)
        plot_combined_kpi_sensitivity_analysis(kpi_sensitivity_results, criterion, kpi_weights, results)
        #print(f"Combined KPI Sensitivity Analysis for {criterion} completed.")

    # Generate subplots for KPI sensitivity analysis across all criteria
    #print("\nGenerating KPI Sensitivity Subplots for all criteria...")
    sensitivity_results_by_criteria = {}
    kpi_weights_by_criteria = {}
    kpi_results_by_criteria = {}

    for criterion, (results, kpi_weights) in zip(
        crit_weights.keys(),
        zip(
            [results_sustainability, results_cost, results_performance, results_risk, results_transportability],
            [kpi_sustainability, kpi_cost, kpi_performance, kpi_risk, kpi_transportability],
        ),
    ):
        kpi_sensitivity_results = perform_kpi_sensitivity_analysis(kpi_weights, results, variation_percentage=0.5)
        sensitivity_results_by_criteria[criterion] = kpi_sensitivity_results
        kpi_weights_by_criteria[criterion] = kpi_weights
        kpi_results_by_criteria[criterion] = results

    plot_kpi_sensitivity_subplots(sensitivity_results_by_criteria, kpi_weights_by_criteria, kpi_results_by_criteria)
    #print("KPI Sensitivity Subplots for all criteria have been saved.")

    # --- Grouped Bar Visualization: Scores with Each Criterion Zeroed ---
    #print("\nGenerating grouped bar visualization: Final scores with each main criterion set to zero weight...")
    plot_grouped_scores_with_criteria_zeroed(crit_weights, calculate_trade_off_scores, results_sustainability['options'])
    #print("Grouped bar visualization saved as 'grouped_scores_with_criteria_zeroed.pdf'.")
