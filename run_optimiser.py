import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from analysis_loops.optimiser_setup import run_optimization

if __name__ == "__main__":
    print("Starting Aircraft Design Optimization...")
    optimization_result, history = run_optimization()
    print("\nOptimization Process Completed.")

    # You can add more code here to save results, plot convergence, etc.
    # For example, to plot how a variable changed during optimization:
    # import matplotlib.pyplot as plt
    # if history:
    #     spans = [p.wing_span_m for p in history]
    #     weights = [p.total_aircraft_weight_kg for p in history]
    #     plt.figure()
    #     plt.subplot(2,1,1)
    #     plt.plot(spans, label='Wing Span (m)')
    #     plt.xlabel("Iteration")
    #     plt.ylabel("Span (m)")
    #     plt.legend()
    #     plt.grid(True)

    #     plt.subplot(2,1,2)
    #     plt.plot(weights, label='Total Weight (kg)', color='r')
    #     plt.xlabel("Iteration")
    #     plt.ylabel("Weight (kg)")
    #     plt.legend()
    #     plt.grid(True)

    #     plt.tight_layout()
    #     plt.show()