# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import cumtrapz

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.unit_conversions import *
from design_variables import *


# ==== Loading Diagrams for UAV Wing Structure ===
#
#
# This code generates loading diagrams for a UAV wing structure based on distributed loads along the span.
# Inputs: 
# - Lift distribution (1D np.array of lift force per unit span)
# - Drag distribution (1D np.array of drag force per unit span)
# - Moment distribution (1D np.array of moment per unit span)
# - Weight distribution (1D np.array of weight per unit span)
# Outputs:          
# - Wing loading diagrams (lift, drag, moment)
# - Internal load distributions (shear force, bending moment, torsion)
# - Total wing weight
#
# =================================================================

class LoadingDiagrams:
    def __init__(self):
        self.SetUp()

    def SetUp(self):
        """
        Set up the loading diagrams parameters and configurations.
        This method initializes the necessary parameters for the loading diagrams calculations.
        """     

        # ==== Load Design Parameters ====
        self.params = DesignParameters()
        self.params.load_from_yaml('design_config.yaml')

        # ==== Generate spanwise mesh (half-span) ====
        self.span = self.params.wing.b_w # Full wingspan = 40 m
        self.y_half = np.linspace(0, self.span / 2, 1000) 

    def compute_resultant_loads(self, lift, drag, moment_aero, weight):
        """
        Compute net vertical load and torque along the span.
        """
        qz = lift - weight  # Net vertical load in z (positive downwards)
        qx = - drag  # Load in negative x-direction (positive drag opposes flight)
        torque = moment_aero  # Aerodynamic moment as distributed torque (about x)
        return qz, qx, torque

    def compute_internal_distributions(self, y, qz, torque_dist):
        """
        Compute internal loads from distributed loading along y-axis (spanwise).
        Inputs:
            - qz: net vertical distributed load (lift - weight), N/m
            - torque_dist: distributed pitching moment + drag-induced torque (Nm/m)
        Output:
            - Vz: shear in z-direction (N)
            - Mx: bending moment about x-axis (Nm)
            - Tx: torsion about x-axis (Nm)
        """

        y_tip_root = y[::-1]  # Reverse y for integration from tip to root


        # Integrate from tip (right) to root (left)
        print(qz)
        Vz_tip_to_root = cumtrapz(qz[::-1], y_tip_root, initial=0)  # Shear force in z-direction
        Mx_tip_to_root = cumtrapz(Vz_tip_to_root, y_tip_root, initial=0)   # Bending moment about x-axis
        Tx_tip_to_root = cumtrapz(torque_dist[::-1], y_tip_root, initial=0)  # Torsion about x-axis

        # Flip back
        Vz = Vz_tip_to_root[::-1]
        Mx = Mx_tip_to_root[::-1]
        Tx = Tx_tip_to_root[::-1]

        return Vz, Mx, Tx

    def plot_internal_loads(self, y, Vz, Mx, Tx, Ny=None, title_prefix=""):
        """
        Plot internal load distributions along the wing half-span.
        
        Parameters:
        - y: spanwise positions (m)
        - Vz: shear force in z-direction (N)
        - Mx: bending moment about x-axis (Nm)
        - Tx: torsion about x-axis (Nm)
        - Ny: (optional) axial force along y-axis (N), if applicable
        - title_prefix: string to prepend to plot titles
        """
        num_plots = 3 + (Ny is not None)
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3.5 * num_plots), sharex=True)

        ax_idx = 0

        axes[ax_idx].plot(y, Vz)
        axes[ax_idx].set_title(f"{title_prefix}Shear Force $V_z$")
        axes[ax_idx].set_ylabel("Shear $V_z$ (N)")
        axes[ax_idx].grid(True)
        ax_idx += 1

        axes[ax_idx].plot(y, Mx)
        axes[ax_idx].set_title(f"{title_prefix}Bending Moment $M_x$")
        axes[ax_idx].set_ylabel("Moment $M_x$ (Nm)")
        axes[ax_idx].grid(True)
        ax_idx += 1

        axes[ax_idx].plot(y, Tx)
        axes[ax_idx].set_title(f"{title_prefix}Torque $T_x$")
        axes[ax_idx].set_ylabel("Torque $T_x$ (Nm)")
        axes[ax_idx].grid(True)
        ax_idx += 1

        if Ny is not None:
            axes[ax_idx].plot(y, Ny)
            axes[ax_idx].set_title(f"{title_prefix}Axial Force $N_y$")
            axes[ax_idx].set_ylabel("Axial $N_y$ (N)")
            axes[ax_idx].grid(True)

        axes[-1].set_xlabel("Spanwise Location y (m)")
        plt.tight_layout()
        plt.show()

    def plot_wing_loading(self, lift_dist, drag_dist, moment_dist):
        """
        Plot wing loading diagrams given the lift, drag, and moment distributions.
        
        Parameters:
        - lift_dist: 1D np.array of lift force per unit span (length 200)
        - drag_dist: 1D np.array of drag force per unit span (length 200)
        - moment_dist: 1D np.array of moment per unit span (length 200)
        """
        # Spanwise locations: from -1 (left tip) to 1 (right tip), 200 points total
        y = np.linspace(-1, 1, 200)

        # Plotting
        plt.figure(figsize=(15, 8))

        plt.subplot(3, 1, 1)
        plt.plot(y, lift_dist)
        plt.title("Lift Distribution Along the Span")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Lift (N/m)")
        plt.grid(True)

        plt.subplot(3, 1, 2)
        plt.plot(y, drag_dist)
        plt.title("Drag Distribution Along the Span")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Drag (N/m)")
        plt.grid(True)

        plt.subplot(3, 1, 3)
        plt.plot(y, moment_dist)
        plt.title("Moment Distribution Along the Span")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Moment (Nm/m)")
        plt.grid(True)

        plt.tight_layout()
        plt.show()

    def plot_wing_weight(weight_dist):
        """
        Plot wing weight distribution along the span and compute total weight.
        
        Parameters:
        - weight_dist: 1D np.array of weight per unit span (N/m), length 200
        """
        y = np.linspace(-1, 1, 200)

        # Total weight via trapezoidal integration
        total_weight = np.trapz(weight_dist, y)

        # Plotting
        plt.figure(figsize=(8, 4))
        plt.plot(y, weight_dist, label='Weight Distribution')
        plt.title("Wing Weight Distribution")
        plt.xlabel("Spanwise Location (y)")
        plt.ylabel("Weight (N/m)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

        print(f"Total Wing Weight: {total_weight:.2f} N")

    def run_analysis_for_case(self, y, lift, drag, moment, weight, label="", PLOT =True):
        """
        Run the loading analysis for a given load case and plot results.
        Parameters:
        - y: spanwise locations (1D np.array)
        - lift: lift distribution (1D np.array)
        - drag: drag distribution (1D np.array)
        - moment: aerodynamic moment distribution (1D np.array)
        - weight: weight distribution (1D np.array)
        - label: optional label for the load case
        - PLOT: boolean to control plotting
        """

        qz, qx, torque = self.compute_resultant_loads(lift, drag, moment, weight)
        Vz, Mx, Tx = self.compute_internal_distributions(y, qz, torque)
        if PLOT:
            self.plot_internal_loads(y, Vz, Mx, Tx, Ny=None, title_prefix=label)
        return Vz, Mx, Tx


if __name__ == "__main__":
    # Initialize the loading diagrams class
    loading_diagrams = LoadingDiagrams()

    # Extract parameters
    params = loading_diagrams.params
    span = params.wing.b_w  # Full wingspan = 40 m
    y_half = loading_diagrams.y_half  # Half-span locations

    # ==== Example Load Case ==== 
    lift = 1000 * (1 - (2 * y_half / span)**2)  # Elliptic lift
    drag = 30 + 5 * np.sin(np.pi * y_half / (span / 2))  # Sinusoidal drag
    moment = 50 * np.cos(np.pi * y_half / (span / 2))  # Aerodynamic pitching moment
    weight = 600 * (1 - (2 * y_half / span)**2)  # Elliptic weight
    # TODO: Apply safety factor to load factor

    loading_diagrams.run_analysis_for_case(y_half, lift, drag, moment, weight, label="Load Case 1 - ")

