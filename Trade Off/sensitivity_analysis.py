import math
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
from trade_off_main import calculate_trade_off_scores, results_sustainability, crit_weights, calculate_weighted_scores, calculate_weighted_scores_from_kpi
from matplotlib import cm
from matplotlib.colors import to_rgba
import colorsys

# Use Arial font
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['font.size'] = 16

def get_distinct_colors(n, alpha=0.7, saturation=0.8):
    if n <= 9:
        base_cmap = cm.get_cmap('Set1')
    elif n <= 20:
        base_cmap = cm.get_cmap('tab20b')
    else:
        base_cmap = cm.get_cmap('nipy_spectral')
    colors = []
    for i in range(n):
        r, g, b, a = to_rgba(base_cmap(i % base_cmap.N), alpha=alpha)
        # Convert RGB to HLS, adjust saturation, then back to RGB
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, min(s * saturation, 1.0))
        colors.append((r2, g2, b2, a))
    return colors


def perform_sensitivity_analysis(base_crit_weights, variation_percentage=0.5):
    base_scores = calculate_trade_off_scores(base_crit_weights)
    sensitivity_results = {}

    for criterion_to_vary in base_crit_weights.keys():
        # Increase weight
        increased_weights = base_crit_weights.copy()
        original_weight = increased_weights[criterion_to_vary]
        increase_amount = original_weight * variation_percentage
        increased_weights[criterion_to_vary] = min(1.0, original_weight + increase_amount)

        # Adjust other weights proportionally to maintain sum of 1
        total_other_weights = sum(w for k, w in base_crit_weights.items() if k != criterion_to_vary)
        if total_other_weights > 0:
            for k in increased_weights.keys():
                if k != criterion_to_vary:
                    increased_weights[k] *= (1.0 - increased_weights[criterion_to_vary]) / total_other_weights

        increased_scores = calculate_trade_off_scores(increased_weights)
        winner_increase = results_sustainability['options'][increased_scores.index(max(increased_scores))]

        # Decrease weight
        decreased_weights = base_crit_weights.copy()
        decrease_amount = original_weight * variation_percentage
        decreased_weights[criterion_to_vary] = max(0.0, original_weight - decrease_amount)

        # Adjust other weights proportionally to maintain sum of 1
        total_other_weights = sum(w for k, w in base_crit_weights.items() if k != criterion_to_vary)
        if total_other_weights > 0:
            for k in decreased_weights.keys():
                if k != criterion_to_vary:
                    decreased_weights[k] *= (1.0 - decreased_weights[criterion_to_vary]) / total_other_weights

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

    sensitivity_results = {}

    for criterion, criterion_results in base_results.items():
        if criterion == "options":
            continue

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
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)
    base_scores = calculate_trade_off_scores(crit_weights)
    options = results_sustainability['options']
    n_options = len(options)
    bar_colors = get_distinct_colors(n_options)
    for criterion, results in sensitivity_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']
        lower_errors = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]
        plt.figure(figsize=(10, 6))
        plt.bar(options, base_scores, color=bar_colors, label='Base Scores')
        plt.errorbar(options, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                     ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars', alpha=0.5)
        plt.title(f"Sensitivity Analysis for {criterion}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.ylim(0.95 * min(base_scores), 1.05 * max(base_scores))
        plt.xticks(options)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.savefig(os.path.join(output_dir, f"sensitivity_{criterion}.pdf"))
        plt.close()


def plot_kpi_sensitivity_analysis(sensitivity_results, criterion, kpi_weights, kpi_results):
    options = list(range(len(next(iter(kpi_results.values())))+1)[1:])
    n_options = len(options)
    bar_colors = get_distinct_colors(n_options)
    for kpi, results in sensitivity_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']
        base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
        lower_errors = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]
        global_min = min(base_scores) - max(lower_errors)
        global_max = max(base_scores) + max(upper_errors)
        plt.figure(figsize=(10, 6))
        plt.bar(options, base_scores, color=bar_colors, label='Base Scores')
        plt.errorbar(options, base_scores, yerr=[lower_errors, upper_errors], fmt='o',
                     ecolor='red', elinewidth=1.5, capsize=5, label='Error Bars', alpha=0.5)
        plt.title(f"KPI Sensitivity Analysis for {criterion} - {kpi}")
        plt.xlabel("Options")
        plt.ylabel("Scores")
        plt.ylim(global_min * 0.95, global_max * 1.05)
        plt.xticks(options)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        plt.savefig(f"Figures/Sensitivity Analysis/KPI Weights/sensitivity_{criterion}_{kpi}.pdf")
        plt.close()


def plot_combined_sensitivity_analysis(sensitivity_results):
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)

    options = results_sustainability['options']
    criteria = list(sensitivity_results.keys())

    base_scores = calculate_trade_off_scores(crit_weights)
    grouped_data = {criterion: base_scores for criterion in criteria}
    lower_errors = {criterion: [] for criterion in criteria}
    upper_errors = {criterion: [] for criterion in criteria}

    for criterion, results in sensitivity_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']
        lower_errors[criterion] = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors[criterion] = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

    x = np.arange(len(options))
    width = 0.15
    intra_group_spacing = 0.05
    inter_group_spacing = 0.2

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = get_distinct_colors(len(criteria))

    for i, (criterion, color) in enumerate(zip(criteria, colors)):
        ax.bar(x + i * (width + intra_group_spacing) + inter_group_spacing * x, grouped_data[criterion], width,
               label=criterion, yerr=[lower_errors[criterion], upper_errors[criterion]],
               capsize=5, alpha=0.8, color=color)
        
    global_min = min(min(base_scores) - max(lower_errors[criterion]) for criterion in criteria)
    global_max = max(max(base_scores) + max(upper_errors[criterion]) for criterion in criteria)

    ax.set_xlabel('Options')
    ax.set_ylabel('Scores')
    plt.ylim(global_min * 0.98, global_max * 1.02)
    ax.set_xticks(x + (width + intra_group_spacing) * (len(criteria) - 1) / 2 + inter_group_spacing * x)
    ax.set_xticklabels(options)
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'combined_sensitivity_analysis.pdf'))
    plt.close()


def plot_combined_kpi_sensitivity_analysis(sensitivity_results, criterion, kpi_weights, kpi_results):
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'KPI Weights')
    os.makedirs(output_dir, exist_ok=True)

    options = list(range(len(next(iter(kpi_results.values())))+1)[1:])
    kpis = list(kpi_weights.keys())

    base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
    grouped_data = {kpi: base_scores for kpi in kpis}
    lower_errors = {kpi: [] for kpi in kpis}
    upper_errors = {kpi: [] for kpi in kpis}

    for kpi, results in sensitivity_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']
        lower_errors[kpi] = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
        upper_errors[kpi] = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

    x = np.arange(len(options))
    width = 0.15
    bar_spacing = 0.05

    fig, ax = plt.subplots(figsize=(12, 8))
    colors = get_distinct_colors(len(kpis))

    for i, (kpi, color) in enumerate(zip(kpis, colors)):
        ax.bar(x + i * (width + bar_spacing), grouped_data[kpi], width, label=kpi,
               yerr=[lower_errors[kpi], upper_errors[kpi]],
               capsize=5, alpha=0.8, color=color)
        
    global_min = min(min(base_scores) - max(lower_errors[kpi]) for kpi in kpis)
    global_max = max(max(base_scores) + max(upper_errors[kpi]) for kpi in kpis)

    ax.set_xlabel('Options')
    ax.set_ylabel('Scores')
    ax.set_ylim(global_min * 0.95, global_max * 1.05)
    ax.set_xticks(x + width * (len(kpis) - 1) / 2)
    ax.set_xticklabels(options)
    ax.legend()

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'combined_kpi_sensitivity_{criterion}.pdf'))
    plt.close()


def plot_kpi_sensitivity_subplots(sensitivity_results_by_criteria, kpi_weights_by_criteria, kpi_results_by_criteria):
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'KPI Weights')
    os.makedirs(output_dir, exist_ok=True)

    num_criteria = len(sensitivity_results_by_criteria)
    num_rows = int(np.ceil(np.sqrt(num_criteria)))
    num_cols = int(np.ceil(num_criteria / num_rows))
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(18, 12))

    # Remove unused subplots and center-align the last row if needed
    total_plots = num_rows * num_cols
    unused = total_plots - num_criteria
    if unused > 0:
        for idx in range(num_criteria, total_plots):
            fig.delaxes(axes.flatten()[idx])
        # Center-align the last row if not full
        last_row = num_rows - 1
        plots_in_last_row = num_criteria % num_cols if num_criteria % num_cols != 0 else num_cols
        if plots_in_last_row < num_cols:
            for col in range(plots_in_last_row, num_cols):
                axes[last_row, col].set_visible(False)
            # Adjust subplot params to center the last row
            fig.subplots_adjust(wspace=0.3, hspace=0.3, bottom=0.08, top=0.95)

    bar_spacing = 0.05
    subplot_labels = [f"({chr(97+i)})" for i in range(num_criteria)]  # (a), (b), ...

    for idx, (criterion, sensitivity_results) in enumerate(sensitivity_results_by_criteria.items()):
        row, col = divmod(idx, num_cols)
        ax = axes[row, col] if num_criteria > 1 else axes
        kpi_weights = kpi_weights_by_criteria[criterion]
        kpi_results = kpi_results_by_criteria[criterion]

        options = list(range(len(next(iter(kpi_results.values())))+1)[1:])
        kpis = list(kpi_weights.keys())

        base_scores = calculate_weighted_scores_from_kpi(kpi_results, kpi_weights)
        grouped_data = {kpi: base_scores for kpi in kpis}
        lower_errors = {kpi: [] for kpi in kpis}
        upper_errors = {kpi: [] for kpi in kpis}

        for kpi, results in sensitivity_results.items():
            increased_scores = results['increased_scores']
            decreased_scores = results['decreased_scores']
            lower_errors[kpi] = [abs(base - dec) for base, dec in zip(base_scores, decreased_scores)]
            upper_errors[kpi] = [abs(inc - base) for base, inc in zip(base_scores, increased_scores)]

        global_min = min(min(base_scores) - max(lower_errors[kpi]) for kpi in kpis)
        global_max = max(max(base_scores) + max(upper_errors[kpi]) for kpi in kpis)

        x = np.arange(len(options))
        width = 0.15

        colors = get_distinct_colors(len(kpis))

        for i, (kpi, color) in enumerate(zip(kpis, colors)):
            ax.bar(x + i * (width + bar_spacing), grouped_data[kpi], width, label=kpi,
                   yerr=[lower_errors[kpi], upper_errors[kpi]],
                   capsize=5, alpha=0.8, color=color)

        ax.set_xlabel('Options', fontsize=16)
        ax.set_ylabel('Scores', fontsize=16)
        ax.set_ylim(global_min * 0.95, global_max * 1.05)
        ax.set_xticks(x + (width + bar_spacing) * (len(kpis) - 1) / 2)
        ax.set_xticklabels(options, fontsize=16)
        ax.legend(fontsize=14)
        ax.grid(axis='y', alpha=0.3)
        ax.annotate(subplot_labels[idx], xy=(0, 1), xycoords='axes fraction',
                    xytext=(-30, 15), textcoords='offset points', fontsize=16,
                    ha='left', va='top', fontweight='normal', annotation_clip=False)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'kpi_sensitivity_subplots.pdf'))
    plt.close()


def min_max_normalize(scores):
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0 for _ in scores]
    return [(s - min_score) / (max_score - min_score) for s in scores]


def plot_scores_with_criteria_zeroed(base_crit_weights, calculate_trade_off_scores_fn, options):
    criteria = list(base_crit_weights.keys())
    num_criteria = len(criteria)
    num_rows = int(np.ceil(np.sqrt(num_criteria)))
    num_cols = int(np.ceil(num_criteria / num_rows))
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(18, 12))

    for idx, criterion in enumerate(criteria):
        zeroed_weights = base_crit_weights.copy()
        zeroed_weights[criterion] = 0.0
        total = sum(zeroed_weights.values())
        if total > 0:
            zeroed_weights = {k: v / total for k, v in zeroed_weights.items()}
        else:
            zeroed_weights = {k: (1.0 if k == criterion else 0.0) for k in zeroed_weights}

        scores = calculate_trade_off_scores_fn(zeroed_weights)
        clipped_scores = [min(5, max(1, s)) for s in scores]
        row, col = divmod(idx, num_cols)
        ax = axes[row, col] if num_criteria > 1 else axes
        colors = get_distinct_colors(len(scores))
        ax.bar(options, clipped_scores, color=colors, width=0.5)
        ax.set_title(f"{criterion} = 0")
        ax.set_xlabel("Options")
        ax.set_ylabel("Final Scores")
        ax.set_ylim(1, 5)
        ax.grid(axis='y', alpha=0.3)
        max_score = max(clipped_scores)
        ax.axhline(y=max_score, color='gray', linestyle='--', label='Max Score')

    for idx in range(num_criteria, num_rows * num_cols):
        fig.delaxes(axes.flatten()[idx])

    plt.tight_layout()
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'scores_with_criteria_zeroed.pdf'))
    plt.close()


def plot_grouped_scores_with_criteria_zeroed(base_crit_weights, calculate_trade_off_scores_fn, options):
    criteria = list(base_crit_weights.keys())
    n_options = len(options)
    n_criteria = len(criteria)
    scores_matrix = []

    for criterion in criteria:
        zeroed_weights = base_crit_weights.copy()
        zeroed_weights[criterion] = 0.0
        total = sum(zeroed_weights.values())
        if total > 0:
            zeroed_weights = {k: v / total for k, v in zeroed_weights.items()}
        else:
            zeroed_weights = {k: (1.0 if k == criterion else 0.0) for k in zeroed_weights}
        scores = calculate_trade_off_scores_fn(zeroed_weights)
        clipped_scores = [min(5, max(1, s)) for s in scores]
        scores_matrix.append(clipped_scores)

    scores_matrix = np.array(scores_matrix)
    width = 0.8 / n_criteria
    intra_group_spacing = 0.03
    inter_group_spacing = 0.2
    x = np.arange(n_options)
    fig, ax = plt.subplots(figsize=(14, 7))
    bar_colors = get_distinct_colors(n_criteria)

    for i, (criterion, color) in enumerate(zip(criteria, bar_colors)):
        ax.bar(x + i * (width + intra_group_spacing) + inter_group_spacing * x, scores_matrix[i], width, label=f"{criterion}", color=color)

    align_idx = 2 if n_criteria > 2 else 0
    ax.set_xticks(x + align_idx * (width + intra_group_spacing) + inter_group_spacing * x)
    ax.set_xticklabels(options, fontsize=16)
    ax.set_xlabel("Options", fontsize=16)
    ax.set_ylabel("Final Score", fontsize=16)
    ax.set_ylim(1, 5)
    ax.legend(title="Criterion with Zero Weight", fontsize=14, title_fontsize=16)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'grouped_scores_with_criteria_zeroed.pdf'))
    plt.close()


def plot_combined_sensitivity_boxplot(sensitivity_results, variation_percentage=1.0):
    """
    Create a boxplot showing the cumulative variation in scores for each option across all criteria weight variations.
    Each box shows the distribution of scores for an option when each criterion is increased and decreased.
    The variation_percentage parameter is used to emphasize the score spread.
    """
    output_dir = os.path.join('Figures', 'Sensitivity Analysis', 'Criteria Weights')
    os.makedirs(output_dir, exist_ok=True)

    options = results_sustainability['options']
    criteria = list(sensitivity_results.keys())
    base_scores = calculate_trade_off_scores(crit_weights)
    n_options = len(options)

    # Recompute sensitivity results with larger variation if needed
    emphasized_results = perform_sensitivity_analysis(crit_weights, variation_percentage=variation_percentage)

    # Collect all score variations for each option
    all_scores = [[] for _ in range(n_options)]
    for criterion, results in emphasized_results.items():
        increased_scores = results['increased_scores']
        decreased_scores = results['decreased_scores']
        for i in range(n_options):
            all_scores[i].append(increased_scores[i])
            all_scores[i].append(decreased_scores[i])

    # Find global min/max for cropping
    all_flat = [score for scores in all_scores for score in scores]
    min_y = min(all_flat)
    max_y = max(all_flat)
    y_margin = (max_y - min_y) * 0.08
    min_y -= y_margin
    max_y += y_margin

    fig, ax = plt.subplots(figsize=(9, 6))
    box = ax.boxplot(all_scores, patch_artist=True, labels=options, showmeans=True)
    box_colors = get_distinct_colors(n_options, alpha=0.7)
    for patch, color in zip(box['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_edgecolor('black')
    for median in box['medians']:
        median.set_color('black')
        median.set_linewidth(2)
    for mean in box['means']:
        mean.set_marker('o')
        mean.set_markerfacecolor('white')
        mean.set_markeredgecolor('black')
        mean.set_markersize(8)


    ax.set_xlabel('Options', fontsize=16)
    ax.set_ylabel('Final Score', fontsize=16)
    ax.set_ylim(min_y, max_y)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'combined_sensitivity_analysis_boxplot.pdf'))
    plt.close()
