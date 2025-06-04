import sys
import os

from analysis_loops.simple_iterator import run_parameter_sweep

if __name__ == "__main__":
    print("Starting Parameter Sweep...")
    sweep_results = run_parameter_sweep()
    print("\nParameter Sweep Finished.")
    # You can add code here to further process or plot sweep_results
    #For example, find the design with the maximum range among feasible designs:
    feasible_designs = [p for p in sweep_results if p.is_feasible]
    if feasible_designs:
        best_by_range = max(feasible_designs, key=lambda p: p.range_km)
        print("\nBest Feasible Design by Range:")
        print(best_by_range)
    else:
        print("\nNo feasible designs found in the sweep.")