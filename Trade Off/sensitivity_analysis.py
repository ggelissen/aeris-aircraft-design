import math
import numpy as np
import matplotlib.pyplot as plt
import os
from trade_off_main import calculate_trade_off_scores, results_sustainability, crit_weights, calculate_weighted_scores, calculate_weighted_scores_from_kpi


def perform_sensitivity_analysis(base_crit_weights, variation_percentage=0.25):
    base_scores = calculate_trade_off_scores(base_crit_weights)
    sensitivity_results = {}

    for criterion_to_vary in base_crit_weights.keys():
        # Increase weight
        increased_weights = base_crit_weights.copy()
        original_weight = increased_weights[criterion_to_vary]
        increase_amount = original_weight * variation_percentage
        increased_weights[criterion_to_vary] = min(1.0, original_weight + increase_amount)
        # Adjust other weights proportionally to maintain sum of 1
        if sum(increased_weights.values()) > 1.0:
            total_other_weights = sum(w for k, w in base_crit_weights.items() if k != criterion_to_vary)
            if total_other_weights > 0:
                for k, w in increased_weights.items():
                    if k != criterion_to_vary:
                        increased_weights[k] = w - (increase_amount * (w / total_other_weights))
                        increased_weights[k] = max(0, increased_weights[k])
            current_sum = sum(increased_weights.values())
            if current_sum > 0:
                increased_weights = {k: v / current_sum for k, v in increased_weights.items()}

        increased_scores = calculate_trade_off_scores(increased_weights)
        winner_increase = results_sustainability['options'][increased_scores.index(max(increased_scores))]

        # Decrease weight
        decreased_weights = base_crit_weights.copy()
        decrease_amount = original_weight * variation_percentage
        decreased_weights[criterion_to_vary] = max(0.0, original_weight - decrease_amount)
        if sum(decreased_weights.values()) < 1.0:
            total_other_weights = sum(w for k, w in base_crit_weights.items() if k != criterion_to_vary)
            if total_other_weights > 0:
                for k, w in decreased_weights.items():
                    if k != criterion_to_vary:
                        decreased_weights[k] = w + (decrease_amount * (w / total_other_weights))
                        decreased_weights[k] = min(1, decreased_weights[k])
            current_sum = sum(decreased_weights.values())
            if current_sum > 0:
                decreased_weights = {k: v / current_sum for k, v in decreased_weights.items()}

        decreased_scores = calculate_trade_off_scores(decreased_weights)
        winner_decrease = results_sustainability['options'][decreased_scores.index(max(decreased_scores))]

        sensitivity_results[criterion_to_vary] = {
            "increased_scores": increased_scores,
            "winner_increase": winner_increase,
            "decreased_scores": decreased_scores,
            "winner_decrease": winner_decrease,
            "increased_weights": {k: round(v, 3) for k, v in increased_weights.items()},
            "decreased_weights": {k: round(v, 3) for k, v in decreased_weights.items()}
        }

    return sensitivity_results


def perform_kpi_sensitivity_analysis(base_kpi_weights, results, variation_percentage=0.25):
    sensitivity_results = {}

    for kpi_to_vary in base_kpi_weights.keys():
        # Increase weight
        increased_weights = base_kpi_weights.copy()
        original_weight = increased_weights[kpi_to_vary]
        increase_amount = original_weight * variation_percentage
        increased_weights[kpi_to_vary] = min(1.0, original_weight + increase_amount)
        # Adjust other weights proportionally to maintain sum of 1
        if sum(increased_weights.values()) > 1.0:
            total_other_weights = sum(w for k, w in base_kpi_weights.items() if k != kpi_to_vary)
            if total_other_weights > 0:
                for k, w in increased_weights.items():
                    if k != kpi_to_vary:
                        increased_weights[k] = w - (increase_amount * (w / total_other_weights))
                        increased_weights[k] = max(0, increased_weights[k])
            current_sum = sum(increased_weights.values())
            if current_sum > 0:
                increased_weights = {k: v / current_sum for k, v in increased_weights.items()}

        increased_scores = calculate_weighted_scores(results, increased_weights)

        # Decrease weight
        decreased_weights = base_kpi_weights.copy()
        decrease_amount = original_weight * variation_percentage
        decreased_weights[kpi_to_vary] = max(0.0, original_weight - decrease_amount)
        if sum(decreased_weights.values()) < 1.0:
            total_other_weights = sum(w for k, w in base_kpi_weights.items() if k != kpi_to_vary)
            if total_other_weights > 0:
                for k, w in decreased_weights.items():
                    if k != kpi_to_vary:
                        decreased_weights[k] = w + (decrease_amount * (w / total_other_weights))
                        decreased_weights[k] = min(1, decreased_weights[k])
            current_sum = sum(decreased_weights.values())
            if current_sum > 0:
                decreased_weights = {k: v / current_sum for k, v in decreased_weights.items()}

        decreased_scores = calculate_weighted_scores(results, decreased_weights)

        sensitivity_results[kpi_to_vary] = {
            "increased_scores": increased_scores,
            "decreased_scores": decreased_scores,
            "increased_weights": {k: round(v, 3) for k, v in increased_weights.items()},
            "decreased_weights": {k: round(v, 3) for k, v in decreased_weights.items()}
        }

    return sensitivity_results


def plot_sensitivity_analysis(sensitivity_results):
    # Ensure the directory for saving figures exists
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)

    base_scores = calculate_trade_off_scores(crit_weights)
    for criterion, results in sensitivity_results.items():
        options = results_sustainability['options']
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']

        # Calculate error bars as the deviation from base scores
        lower_errors = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

        # Create bar plot with differentiated error bars
        plt.figure(figsize=(10, 6))
        plt.bar(options, base_scores, color='skyblue', label='Base Scores')
        plt.errorbar(options, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                     ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars')
        plt.title(f"Sensitivity Analysis for {criterion}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.ylim(0.95*min(base_scores),1.05*max(base_scores))
        plt.xticks(options)
        plt.legend()
        plt.grid(axis='y')
        plt.savefig(os.path.join(output_dir, f"sensitivity_{criterion}.pdf"))
        plt.close()


def plot_kpi_sensitivity_analysis(sensitivity_results, criterion, kpi_weights, kpi_results):
    options = list(range(len(next(iter(kpi_results.values()))))) 

    for kpi, results in sensitivity_results.items():
        if kpi not in kpi_results:
            raise KeyError(f"The KPI '{kpi}' is missing in the provided kpi_results for {criterion}.")

        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']

        # Calculate error bars as the deviation from base scores
        base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
        lower_errors = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

        # Create bar plot with differentiated error bars
        plt.figure(figsize=(10, 6))
        plt.bar(options, base_scores, color='skyblue', label='Base Scores')
        plt.errorbar(options, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                     ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars')
        plt.title(f"KPI Sensitivity Analysis for {criterion} - {kpi}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.ylim(0.95 * min(base_scores), 1.05 * max(base_scores))
        plt.xticks(options)
        plt.legend()
        plt.grid(axis='y')
        plt.savefig(f"Figures/Sensitivity Analysis/KPI Weights/sensitivity_{criterion}_{kpi}.pdf")
        plt.close()


def plot_combined_sensitivity_analysis(sensitivity_results):
    # Ensure the directory for saving figures exists
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)

    options = results_sustainability['options']
    criteria = list(sensitivity_results.keys())

    # Initialize data for the grouped bar plot
    base_scores = calculate_trade_off_scores(crit_weights)
    grouped_data = {criterion: base_scores for criterion in criteria}
    lower_errors = {criterion: [] for criterion in criteria}
    upper_errors = {criterion: [] for criterion in criteria}

    for criterion, results in sensitivity_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']

        # Calculate error bars as the deviation from base scores
        lower_errors[criterion] = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors[criterion] = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

    # Create the grouped bar plot
    x = np.arange(len(options))  # the label locations
    width = 0.15  # the width of the bars
    intra_group_spacing = 0.05  # spacing between criteria within a group
    inter_group_spacing = 0.2  # spacing between groups (options)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Define a blue gradient for the bars
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(criteria)))

    for i, (criterion, color) in enumerate(zip(criteria, colors)):
        ax.bar(x + i * (width + intra_group_spacing) + inter_group_spacing * x, grouped_data[criterion], width,
               label=criterion, yerr=[lower_errors[criterion], upper_errors[criterion]],
               capsize=5, alpha=0.8, color=color)

    # Add labels, title, and legend
    ax.set_xlabel('Options')
    ax.set_ylabel('Scores')
    plt.ylim(0.475, max(base_scores) * 1.05)
    ax.set_title('Combined Sensitivity Analysis')
    ax.set_xticks(x + (width + intra_group_spacing) * (len(criteria) - 1) / 2 + inter_group_spacing * x)
    ax.set_xticklabels(options)
    ax.legend()

    # Save the plot
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'combined_sensitivity_analysis.pdf'))
    plt.close()