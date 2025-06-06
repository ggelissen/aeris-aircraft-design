# _____ IMPORTS _____
import sys
import os
import yaml
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.integrate import cumtrapz, cumulative_trapezoid

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

class WingLoadingDiagrams:
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
        self.y = np.linspace(0, self.span / 2, 1000)  # Half-span from root to tip

        # ==== Initialize arrays for distributed loads ====
        #
        # -> NOTE: These are example distributions. In practice, these would be calculated based on aerodynamic analysis and wing weight.
        self.lift = 1000 * (1 - (2 * self.y / self.span)**2)  # Elliptic lift
        self.drag = 30 + 5 * np.sin(np.pi * self.y / (self.span / 2))  # Sinusoidal drag
        self.moment_aero = 50 * np.cos(np.pi * self.y / (self.span / 2))  # Aerodynamic pitching moment
        self.weight = 600 * (1 - (2 * self.y / self.span)**2)  # Elliptic weight

    def compute_resultant_loads(self, lift, drag, moment_aero, weight):
        """
        Compute net vertical load and torque along the span.
        Inputs:
            - lift: 1D np.array of lift force per unit span (N/m)
            - drag: 1D np.array of drag force per unit span (N/m)
            - moment_aero: 1D np.array of aerodynamic moment per unit span (Nm/m)
            - weight: 1D np.array of weight per unit span (N/m)
        Outputs:
            - force_z: net distributed vertical load in z-direction (N)
            - force_x: net distributed load in x-direction (N)
            - torque_y: distributed torque about y-axis (Nm/m)
        """
        # Net Distributes Loads
        force_z = - lift + weight  # net distributed vertical load in z (positive downwards)
        force_x = - drag  # net distributed horizontal load in negative x-direction (positive towards nose)

        # For Torque: Aerod. Moment + Induced Torque (from Vertical/Horizontal Forces)
        x_distance_SC_AC = 0.01  # X-axis distance from reference load point to shear center (m)
        z_distance_SC_AC = 0.01  # Z-axis distance from reference load point to shear center (m)
        moment_aerodynamic_to_shear_center = - (force_x * z_distance_SC_AC + force_z * x_distance_SC_AC)  # induced torque from forces about y-axis

        # Total torque about y-axis
        torque_y = moment_aero + moment_aerodynamic_to_shear_center # distributed torque about y-axis (postice Right-handed system)
        

        return force_z, force_x, torque_y

    def compute_internal_distributions(self, y, force_z, force_x, torque_y):
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

        y_tip_root = np.flip(y)  # Reverse y for integration from tip to root

        # Integrate from tip (right) to root (left)
    
        # Distributed Load in z-direction
        Vz_tip_to_root = cumtrapz(force_z[::-1], y_tip_root, initial=0)  # Shear force in z-direction
        # Note: The bending moment about x-axis is due to the shear force in z-direction
        Mx_tip_to_root = cumtrapz(Vz_tip_to_root, y_tip_root, initial=0)   # Bending moment about x-axis

        # Distributed Load in x-direction
        Vx_tip_to_root = cumtrapz(force_x[::-1], y_tip_root, initial=0)  # Shear force in x-direction
        # Note: The bending moment about z-axis is due to the shear force in x-direction
        Mz_tip_to_root = cumtrapz(Vx_tip_to_root, y_tip_root, initial=0)  # Bending moment about z-axis

        # Torsion about y-axis
        Ty_tip_to_root = cumtrapz(torque_y[::-1], y_tip_root, initial=0)  # Torsion about y-axis

        # Flip back -> root to tip
        shear_z = Vz_tip_to_root[::-1]
        bend_moment_x = Mx_tip_to_root[::-1]
        shear_x = Vx_tip_to_root[::-1]
        bend_moment_z = Mz_tip_to_root[::-1]
        torsion_y = Ty_tip_to_root[::-1]

        internal_loads = {
            'shear_z': shear_z,
            'bend_moment_x': bend_moment_x,
            'torsion_y': torsion_y,
            'shear_x': shear_x,
            'bend_moment_z': bend_moment_z
        }
 
        return internal_loads

    def plot_internal_loads(self, y, Vz, Mx, Tx, Vx, Mz, title_prefix=""):
        """
        Plot internal load distributions along the wing half-span.

        Parameters:
        - y: spanwise positions (m)
        - Vz: shear force in z-direction (N)
        - Mx: bending moment about x-axis (Nm)
        - Tx: torsion about x-axis (Nm)
        - Vx: (optional) shear force in x-direction (N)
        - Mz: (optional) bending moment about z-axis (Nm)
        - title_prefix: string to prepend to plot titles
        """
        components = [
            (Vz, "Shear Force $V_z$", "Shear $V_z$ (N)"),
            (Mx, "Bending Moment $M_x$", "Moment $M_x$ (Nm)"),
            (Tx, "Torque $T_x$", "Torque $T_x$ (Nm)"),
            (Vx, "Shear Force $V_x$", "Shear $V_x$ (N)"),
            (Mz, "Bending Moment $M_z$", "Moment $M_z$ (Nm)")
        ]

    
        num_plots = len(components)
        fig, axes = plt.subplots(num_plots, 1, figsize=(12, 3.5 * num_plots), sharex=True)

        for ax, (data, title, ylabel) in zip(axes, components):
            ax.plot(y, data)
            ax.set_title(f"{title_prefix}{title}")
            ax.set_ylabel(ylabel)
            ax.grid(True)

        axes[-1].set_xlabel("Spanwise Location y (m)")
        plt.tight_layout()
        plt.show()

    def plot_wing_aerodynamic_loading(self, lift_dist, drag_dist, moment_dist):
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

    def run_analysis(self, PLOT):
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

        force_z, force_x, torque_y = self.compute_resultant_loads(self.lift, self.drag, self.moment_aero, self.weight)
        shear_z, bend_moment_x, torsion_y, shear_x, bend_moment_z = self.compute_internal_distributions(self.y, force_z, force_x, torque_y)
        if PLOT:
            self.plot_internal_loads(self.y, shear_z, bend_moment_x, torsion_y, shear_x, bend_moment_z, title_prefix="")
        return shear_z, bend_moment_x, torsion_y, shear_x, bend_moment_z






if __name__ == "__main__":
    # Initialize the loading diagrams class
    
    internal_loads = WingLoadingDiagrams().run_analysis(PLOT=False)

    print(internal_loads)



