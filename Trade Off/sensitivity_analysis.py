import math
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
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
        total_other_weights = sum(w for k, w in base_kpi_weights.items() if k != kpi_to_vary)
        if total_other_weights > 0:
            for k in increased_weights.keys():
                if k != kpi_to_vary:
                    increased_weights[k] *= (1.0 - increased_weights[kpi_to_vary]) / total_other_weights

        increased_scores = calculate_weighted_scores(results, increased_weights)

        # Decrease weight
        decreased_weights = base_kpi_weights.copy()
        decrease_amount = original_weight * variation_percentage
        decreased_weights[kpi_to_vary] = max(0.0, original_weight - decrease_amount)

        # Adjust other weights proportionally to maintain sum of 1
        total_other_weights = sum(w for k, w in base_kpi_weights.items() if k != kpi_to_vary)
        if total_other_weights > 0:
            for k in decreased_weights.keys():
                if k != kpi_to_vary:
                    decreased_weights[k] *= (1.0 - decreased_weights[kpi_to_vary]) / total_other_weights

        decreased_scores = calculate_weighted_scores(results, decreased_weights)

        sensitivity_results[kpi_to_vary] = {
            "increased_scores": increased_scores,
            "decreased_scores": decreased_scores,
            "increased_weights": {k: round(v, 3) for k, v in increased_weights.items()},
            "decreased_weights": {k: round(v, 3) for k, v in decreased_weights.items()}
        }

    return sensitivity_results


def perform_result_sensitivity_analysis(base_results, variation_percentage=0.25, calculate_final_scores=None):
    """
    Perform sensitivity analysis on the input scores (results).

    Args:
        base_results (dict): The base results for each criterion and option.
        variation_percentage (float): The percentage by which to vary the input scores.
        calculate_final_scores (function): A function to calculate final scores based on modified results.

    Returns:
        dict: Sensitivity results for each criterion and option, including propagated final scores.
    """
    logging.debug("Starting result sensitivity analysis.")
    logging.debug(f"Base Results: {base_results}")

    sensitivity_results = {}

    for criterion, criterion_results in base_results.items():
        if criterion == "options":
            continue

        logging.debug(f"Analyzing criterion: {criterion}")
        criterion_sensitivity = {}

        for option_index, base_score in enumerate(criterion_results):
            # Increase score
            increased_score = base_score * (1 + variation_percentage)
            increased_results = criterion_results.copy()
            increased_results[option_index] = increased_score

            # Decrease score
            decreased_score = base_score * (1 - variation_percentage)
            decreased_results = criterion_results.copy()
            decreased_results[option_index] = decreased_score

            criterion_sensitivity[option_index] = {
                "increased_results": increased_results,
                "decreased_results": decreased_results
            }

        sensitivity_results[criterion] = criterion_sensitivity

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
        plt.ylim(0.95 * min(base_scores), 1.05 * max(base_scores))
        plt.xticks(options)
        plt.legend()
        plt.grid(axis='y')
        plt.savefig(os.path.join(output_dir, f"sensitivity_{criterion}.pdf"))
        plt.close()


def plot_result_sensitivity_analysis(sensitivity_results, base_results):
    """
    Plot the sensitivity analysis for input scores (results).

    Args:
        sensitivity_results (dict): Sensitivity results for each criterion and option.
        base_results (dict): The base results for each criterion and option.
    """
    logging.debug("Plotting result sensitivity analysis.")

    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Inputs')
    os.makedirs(output_dir, exist_ok=True)

    options = base_results["options"]

    for criterion, criterion_sensitivity in sensitivity_results.items():
        if criterion == "options":
            continue

        logging.debug(f"Plotting sensitivity for criterion: {criterion}")

        plt.figure(figsize=(10, 6))

        for option_index, sensitivity in criterion_sensitivity.items():
            base_score = base_results[criterion][option_index]
            increased_score = sensitivity["increased_results"][option_index]
            decreased_score = sensitivity["decreased_results"][option_index]

            # Plot base, increased, and decreased scores
            plt.bar(option_index - 0.2, base_score, width=0.2, color='skyblue', label='Base Score' if option_index == 0 else "")
            plt.bar(option_index, increased_score, width=0.2, color='green', label='Increased Score' if option_index == 0 else "")
            plt.bar(option_index + 0.2, decreased_score, width=0.2, color='red', label='Decreased Score' if option_index == 0 else "")

        plt.title(f"Result Sensitivity Analysis for {criterion}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.xticks(range(len(options)), options)
        plt.legend()
        plt.grid(axis='y')
        plt.savefig(os.path.join(output_dir, f"sensitivity_results_{criterion}.pdf"))
        plt.close()


def plot_kpi_sensitivity_analysis(sensitivity_results, criterion, kpi_weights, kpi_results):

    options = list(range(len(next(iter(kpi_results.values())))))

    for kpi, results in sensitivity_results.items():

        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']

        # Calculate error bars as the deviation from base scores
        base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
        lower_errors = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

        # Global minimum and maximum values for y-axis scaling
        global_min = min(base_scores) - max(lower_errors)
        global_max = max(base_scores) + max(upper_errors)

        # Create bar plot with differentiated error bars
        plt.figure(figsize=(10, 6))
        plt.bar(options, base_scores, color='skyblue', label='Base Scores')
        plt.errorbar(options, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                     ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars')
        plt.title(f"KPI Sensitivity Analysis for {criterion} - {kpi}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.ylim(global_min * 0.95, global_max * 1.05)
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
        
    # Calculate global minimum and maximum values for y-axis scaling based on changed scores
    global_min = min(min(base_scores) - max(lower_errors[criterion]) for criterion in criteria)
    global_max = max(max(base_scores) + max(upper_errors[criterion]) for criterion in criteria)

    # Add labels, title, and legend
    ax.set_xlabel('Options')
    ax.set_ylabel('Scores')
    plt.ylim(global_min * 0.98, global_max * 1.02)
    ax.set_title('Combined Sensitivity Analysis')
    ax.set_xticks(x + (width + intra_group_spacing) * (len(criteria) - 1) / 2 + inter_group_spacing * x)
    ax.set_xticklabels(options)
    ax.legend()

    # Save the plot
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'combined_sensitivity_analysis.pdf'))
    plt.close()


def plot_combined_kpi_sensitivity_analysis(sensitivity_results, criterion, kpi_weights, kpi_results):
    # Ensure the directory for saving figures exists
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'KPI Weights')
    os.makedirs(output_dir, exist_ok=True)

    options = list(range(len(next(iter(kpi_results.values())))))  # Infer options from KPI results
    kpis = list(kpi_weights.keys())

    # Initialize data for the grouped bar plot
    base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
    grouped_data = {kpi: base_scores for kpi in kpis}
    lower_errors = {kpi: [] for kpi in kpis}
    upper_errors = {kpi: [] for kpi in kpis}

    # Correctly calculate error bars for combined KPI sensitivity analysis for all KPIs
    for kpi, results in sensitivity_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']

        # Calculate error bars as the deviation from base scores
        lower_errors[kpi] = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors[kpi] = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

    # Create the grouped bar plot
    x = np.arange(len(options))  # the label locations
    width = 0.15  # the width of the bars
    bar_spacing = 0.05  # Adjust spacing as needed

    fig, ax = plt.subplots(figsize=(12, 8))

    # Use a blue gradient for the bars
    colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(kpis)))

    for i, (kpi, color) in enumerate(zip(kpis, colors)):
        ax.bar(x + i * (width + bar_spacing), grouped_data[kpi], width, label=kpi,
               yerr=[lower_errors[kpi], upper_errors[kpi]],
               capsize=5, alpha=0.8, color=color)
        
    # Calculate global minimum and maximum values for y-axis scaling based on changed scores
    global_min = min(min(base_scores) - max(lower_errors[kpi]) for kpi in kpis)
    global_max = max(max(base_scores) + max(upper_errors[kpi]) for kpi in kpis)

    # Add labels, title, and legend
    ax.set_xlabel('Options')
    ax.set_ylabel('Scores')
    ax.set_title(f'Combined KPI Sensitivity Analysis for {criterion}')
    ax.set_ylim(global_min * 0.95, global_max * 1.05)
    ax.set_xticks(x + width * (len(kpis) - 1) / 2)
    ax.set_xticklabels(options)
    ax.legend()

    # Save the plot
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'combined_kpi_sensitivity_{criterion}.pdf'))
    plt.close()


def plot_kpi_sensitivity_subplots(sensitivity_results_by_criteria, kpi_weights_by_criteria, kpi_results_by_criteria):
    # Ensure the directory for saving figures exists
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'KPI Weights')
    os.makedirs(output_dir, exist_ok=True)

    num_criteria = len(sensitivity_results_by_criteria)
    num_rows = int(np.ceil(np.sqrt(num_criteria)))
    num_cols = int(np.ceil(num_criteria / num_rows))
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(18, 12))

    # Adjust layout to remove unused subplot and center the bottom plot
    if num_criteria < num_rows * num_cols:
        for idx in range(num_criteria, num_rows * num_cols):
            fig.delaxes(axes.flatten()[idx])

    # Add slight spacing between bars
    bar_spacing = 0.05  # Adjust spacing as needed

    for idx, (criterion, sensitivity_results) in enumerate(sensitivity_results_by_criteria.items()):
        row, col = divmod(idx, num_cols)
        ax = axes[row, col] if num_criteria > 1 else axes
        kpi_weights = kpi_weights_by_criteria[criterion]
        kpi_results = kpi_results_by_criteria[criterion]

        options = list(range(len(next(iter(kpi_results.values())))))  # Infer options from KPI results
        kpis = list(kpi_weights.keys())

        # Initialize data for the grouped bar plot
        base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
        grouped_data = {kpi: base_scores for kpi in kpis}
        lower_errors = {kpi: [] for kpi in kpis}
        upper_errors = {kpi: [] for kpi in kpis}

        for kpi, results in sensitivity_results.items():
            increased_scores = results['increased_scores']
            decreased_scores = results['decreased_scores']

            # Calculate error bars as the deviation from base scores
            lower_errors[kpi] = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
            upper_errors[kpi] = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

        # Calculate global minimum and maximum values for y-axis scaling based on error bars
        global_min = min(min(base_scores) - max(lower_errors[kpi]) for kpi in kpis)
        global_max = max(max(base_scores) + max(upper_errors[kpi]) for kpi in kpis)

        # Create the grouped bar plot for the current criterion
        x = np.arange(len(options))  # the label locations
        width = 0.15  # the width of the bars

        # Use a blue gradient for the bars
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(kpis)))

        for i, (kpi, color) in enumerate(zip(kpis, colors)):
            ax.bar(x + i * (width + bar_spacing), grouped_data[kpi], width, label=kpi,
                   yerr=[lower_errors[kpi], upper_errors[kpi]],
                   capsize=5, alpha=0.8, color=color)

        # Add labels, title, and legend
        ax.set_xlabel('Options')
        ax.set_ylabel('Scores')
        ax.set_title(f'KPI Sensitivity Analysis for {criterion}')
        ax.set_ylim(global_min * 0.95, global_max * 1.05)
        ax.set_xticks(x + (width + bar_spacing) * (len(kpis) - 1) / 2)
        ax.set_xticklabels(options)
        ax.legend()

    # Adjust layout for square grid
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'kpi_sensitivity_subplots.pdf'))
    plt.close()


def plot_combined_result_sensitivity_analysis(sensitivity_results, base_results):
    """
    Combine all KPIs into one plot per criterion with increased and decreased scores using error bars.

    Args:
        sensitivity_results (dict): Sensitivity results for each criterion and option.
        base_results (dict): The base results for each criterion and option.
    """
    logging.debug("Plotting combined result sensitivity analysis.")

    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Inputs')
    os.makedirs(output_dir, exist_ok=True)

    options = base_results["options"]

    for criterion, criterion_sensitivity in sensitivity_results.items():
        if criterion == "options":
            continue

        logging.debug(f"Plotting combined sensitivity for criterion: {criterion}")

        # Initialize data for the grouped bar plot
        base_scores = base_results[criterion]
        lower_errors = []
        upper_errors = []

        for option_index, sensitivity in criterion_sensitivity.items():
            increased_score = sensitivity["increased_results"][option_index]
            decreased_score = sensitivity["decreased_results"][option_index]

            lower_errors.append(abs(base_scores[option_index] - decreased_score))
            upper_errors.append(abs(increased_score - base_scores[option_index]))

        # Create the plot
        x = np.arange(len(options))  # the label locations

        plt.figure(figsize=(10, 6))
        plt.bar(x, base_scores, color='skyblue', label='Base Scores')
        plt.errorbar(x, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                     ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars')

        plt.title(f"Combined Result Sensitivity Analysis for {criterion}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.xticks(x, options)
        plt.legend()
        plt.grid(axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f"combined_sensitivity_results_{criterion}.pdf"))
        plt.close()


def plot_result_sensitivity_subplots(sensitivity_results_by_criteria, base_results_by_criteria):
    """
    Create a big plot with all criteria as subplots for result sensitivity analysis.

    Args:
        sensitivity_results_by_criteria (dict): Sensitivity results for all criteria.
        base_results_by_criteria (dict): Base results for all criteria.
    """
    logging.debug("Plotting result sensitivity subplots.")

    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Inputs')
    os.makedirs(output_dir, exist_ok=True)

    num_criteria = len(sensitivity_results_by_criteria)
    num_rows = int(np.ceil(np.sqrt(num_criteria)))
    num_cols = int(np.ceil(num_criteria / num_rows))
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(18, 12))

    # Adjust layout to remove unused subplot and center the bottom plot
    if num_criteria < num_rows * num_cols:
        for idx in range(num_criteria, num_rows * num_cols):
            fig.delaxes(axes.flatten()[idx])

    for idx, (criterion, sensitivity_results) in enumerate(sensitivity_results_by_criteria.items()):
        row, col = divmod(idx, num_cols)
        ax = axes[row, col] if num_criteria > 1 else axes

        base_scores = base_results_by_criteria[criterion]
        lower_errors = []
        upper_errors = []

        for option_index, sensitivity in sensitivity_results.items():
            increased_score = sensitivity["increased_results"][option_index]
            decreased_score = sensitivity["decreased_results"][option_index]

            lower_errors.append(abs(base_scores[option_index] - decreased_score))
            upper_errors.append(abs(increased_score - base_scores[option_index]))

        x = np.arange(len(base_results_by_criteria["options"]))  # the label locations

        # Use a blue gradient for the bars
        colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(base_scores)))

        ax.bar(x, base_scores, color=colors, label='Base Scores')
        ax.errorbar(x, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                    ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars')

        ax.set_title(f"{criterion}")
        ax.set_xlabel("Options")
        ax.set_ylabel("Scores")
        ax.set_xticks(x)
        ax.set_xticklabels(base_results_by_criteria["options"])
        ax.legend()
        ax.grid(axis='y')

    # Adjust layout for square grid
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'result_sensitivity_subplots.pdf'))
    plt.close()