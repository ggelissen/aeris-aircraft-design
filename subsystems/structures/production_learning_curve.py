import numpy as np
import math as m
import matplotlib.pyplot as plt


def learning_curve(W_ampr: float, V_max: float, N_program: np.ndarray, F_diff: float):
    """
    Calculate the learning curve for a given aircraft design.

    Parameters:
    W_ampr (float): Maximum takeoff weight in kg.
    V_max (float): Maximum speed in m/s.
    N_program (int): Number of programs or iterations.
    F_diff (float): Factor for the learning curve.

    Returns:
    tuple: Array of number of man-hours required (MHR) for each program.
    """
    MHR = 28.984 * W_ampr ** 0.74 * V_max ** 0.543 * N_program ** 0.524 * F_diff
    return MHR

def plot_learning_curve(N_program: np.ndarray, MHR: np.ndarray):
    """
    Plot the learning curve.

    Parameters:
    N_program (np.ndarray): Array of program iterations.
    MHR (np.ndarray): Array of calculated MHR values.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(N_program, MHR/N_program/1000, marker='', linestyle='-', color='b', linewidth=3)
    plt.xlabel('Production Volume [Units]', fontsize=14)
    plt.ylabel(r'Man Hours [$h \cdot 10^3$]', fontsize=14)
    plt.tick_params(axis='both', which='major', labelsize=14)
    plt.grid()
    plt.savefig('Figures/learning_curve.pdf')


if __name__ == "__main__":

    W_ampr = 1683  # Maximum takeoff weight in kg
    V_max = 544      # Maximum speed in m/s
    N_produced = np.linspace(1, 2000, 100)
    N_program = N_produced + 4
    F_diff = 1.25     # Learning curve factor

    # Calculate learning curve
    MHR = learning_curve(W_ampr, V_max, N_program, F_diff) - 558858.42 

    # Plot the learning curve
    plot_learning_curve(N_produced, MHR)
    print("Learning curve calculated and plotted successfully.")