import math
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from design_variables import DesignParameters
from subsystems.flightperformance.utils_flight import __ISA__
from subsystems.flightperformance.FlightSim import FlightSim
from subsystems.flightperformance.take_off_requirement import calculate_Cm

# --- Plotting Style and Formatting ---

def _set_report_style():
    """Sets a professional plot style suitable for reports."""
    try:
        plt.rcParams['font.family'] = 'Arial'
    except RuntimeError:
        print("Arial font not found, falling back to default sans-serif.")
        plt.rcParams['font.family'] = 'sans-serif'
    
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 300
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['lines.linewidth'] = 2.5
    plt.rcParams['lines.markersize'] = 6

COLOR_PALETTE = {
    'blue': '#0d3b66',
    'orange': '#ee964b',
    'grey': '#4F4F4F',
    'green': '#5fad56',
    'red': '#D7263D'
}


class FlightPerformance:
    def __init__(self):
        pass
    
    def __drag__(self, cd0, rho, V, S, W, A, oswald, C_L=None):
        if C_L == None:
            C_L = W/(0.5*rho*V**2*S)
        D0 = cd0 * 0.5 * rho * V**2 * S
        Di = (C_L**2)/(math.pi * A * oswald) * 0.5 * rho * V**2 * S
        D = D0 + Di
        return D, D0, Di
    
    def __trim_drag__(self, rho, V, V_h_V, S_h, A_h, e_h, CL_h):
        D_trim = (0.5 * rho * V**2 * (V_h_V)**2 * S_h * CL_h**2)/(np.pi*A_h*e_h)
        return D_trim
        
    def drag_plot(self, cd0, rho, V_range, S, W, A, oswald, V_stall):
        """
        Generates a styled plot of drag components vs. velocity, cropped to a useful view.
        """
        _set_report_style()
        V_flight = V_range[V_range >= V_stall]
        
        if len(V_flight) < 2:
            print("Warning: Not enough data points above stall speed to generate drag plot.")
            return

        D, D0, Di = self.__drag__(cd0, rho, V_flight, S, W, A, oswald)
        
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.plot(V_flight, D, label="Total Drag", color=COLOR_PALETTE['blue'])
        ax.plot(V_flight, D0, label="Zero-lift (Parasitic) Drag", color=COLOR_PALETTE['orange'], linestyle='--')
        ax.plot(V_flight, Di, label="Lift-induced Drag", color=COLOR_PALETTE['green'], linestyle='--')
        ax.axvline(x=V_stall, color=COLOR_PALETTE['red'], linestyle=':', linewidth=2, label=f'$V_{{stall}} = {V_stall:.1f}$ m/s')

        # --- Intelligent Cropping ---
        # Find minimum drag and set y-limit to a multiple of that for a good view
        min_drag = np.min(D)
        ax.set_ylim(bottom=0, top=min_drag * 3) # Crop view to 3x minimum drag
        ax.set_xlim(left=V_stall-20)

        #ax.set_title('Drag Components vs. Airspeed')
        ax.set_xlabel('Velocity ($V_{EAS}$) [m/s]')
        ax.set_ylabel('Drag ($D$) [N]')
        ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='lightgrey')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        legend = ax.legend(loc='best', frameon=True)
        frame = legend.get_frame()
        frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
        frame.set_facecolor('white')
        frame.set_edgecolor('black')
        frame.set_alpha(0.8)
        legend.set_zorder(10)
        
        plt.tight_layout()
        os.makedirs("Figures", exist_ok=True)
        plt.savefig("Figures/flight performance/drag_plot.pdf", transparent=False)
        plt.close(fig)
        print("Saved plot: Figures/flight performance/drag_plot.pdf")

    def __range__(self, cT, W_ini, W_fin, A, oswald, cd0, rho, S):
        C_L = (1/3 * math.pi * A * oswald * cd0)**0.5
        C_D = 4/3* cd0
        R = 2 * (2/(rho*S))**0.5 * 1/(cT*0.000001 * 9.81) * (C_L**0.5)/C_D * (W_ini**0.5 - W_fin**0.5)
        return R/1000

    def payload_range(self, cT, A, oswald, cd0, Wtotal, Wfuel, OEW, rho, S, plot=False):
        Wpayload = np.arange(0, Wtotal-Wfuel-OEW, 1*9.81)
        ranges = []
        for payload in Wpayload:
            range1 = self.__range__(cT, OEW + Wfuel + payload, OEW + payload, A, oswald, cd0, rho, S)
            ranges.append(range1)
        
        if plot:
            self._plot_payload_range(ranges, Wpayload)
            
        return (min(ranges), max(ranges))

    def _plot_payload_range(self, ranges, Wpayload):
        """Generates a styled payload-range diagram."""
        _set_report_style()
        fig, ax = plt.subplots(figsize=(8, 5))
        
        max_payload_kg = np.max(Wpayload) / 9.81
        ferry_range = np.min(ranges)
        print('ferry_Range',ferry_range)

        # Plot the main curve
        ax.plot(ranges, Wpayload / 9.81, color=COLOR_PALETTE['blue'])
        # Plot the ferry range segment
        ax.plot([0, ferry_range], [max_payload_kg, max_payload_kg], color=COLOR_PALETTE['blue'], linestyle='--')
        
        # --- Aesthetics ---
        #ax.set_title('Payload-Range Diagram')
        ax.set_xlabel('Range ($R$) [km]')
        ax.set_ylabel('Payload Mass ($M_{PL}$) [kg]')
        ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='lightgrey')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        plt.tight_layout()
        os.makedirs("Figures", exist_ok=True)
        plt.savefig("Figures/flight performance/payload_range.pdf", transparent=False)
        plt.close(fig)
        print("Saved plot: Figures/flight performance/payload_range.pdf")

    def ROC(self, cd0, rho, V_range, S, W, A, oswald, T, V_stall, plot=False):
        """Calculates Rate of Climb, corrected for stall speed."""
        V_flight = V_range[V_range >= V_stall]
        if len(V_flight) < 2:
            return 0, 0, 0, 0

        D, _, _ = self.__drag__(cd0, rho, V_flight, S, W, A, oswald)
        
        AOC = (T - min(D)) / W
        AOC_V = V_flight[np.argmin(D)]
        print('T',T)
        if plot:
            self._plot_roc_forces(V_flight, D, T, V_stall)

        ROC = (V_flight * T - V_flight * D) / W
        max_ROC = np.max(ROC)
        ROC_V = V_flight[np.argmax(ROC)]
        
        if plot:
            self._plot_roc_power(V_flight, V_flight * D, V_flight * T, V_stall)
            
        return AOC, AOC_V, max_ROC, ROC_V

    def _plot_roc_forces(self, V, D, T, V_stall):
        """Generates a styled Thrust vs. Drag plot with a useful view."""
        _set_report_style()
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.plot(V, [T] * len(V), label='Thrust Available', color=COLOR_PALETTE['green'])
        ax.plot(V, D, label='Total Drag (Power Required)', color=COLOR_PALETTE['blue'])
        ax.fill_between(V, T, D, where=(T > D), color=COLOR_PALETTE['green'], alpha=0.1, label='Excess Thrust')
        ax.axvline(x=V_stall, color=COLOR_PALETTE['red'], linestyle=':', linewidth=2, label=f'$V_{{stall}} = {V_stall:.1f}$ m/s')

        # --- Intelligent Cropping ---
        # Set y-limit based on thrust available for a clean view
        ax.set_ylim(bottom=0, top=T * 1.5)
        ax.set_xlim(left=0)

        #ax.set_title('Thrust and Drag vs. Airspeed')
        ax.set_xlabel('Velocity ($V_{EAS}$) [m/s]')
        ax.set_ylabel('Force ($F$) [N]')
        ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='lightgrey')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        legend = ax.legend(loc='best', frameon=True)
        frame = legend.get_frame()
        frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
        frame.set_facecolor('white')
        frame.set_edgecolor('black')
        frame.set_alpha(0.8)
        legend.set_zorder(10)
        
        plt.tight_layout()
        os.makedirs("Figures", exist_ok=True)
        plt.savefig("Figures/flight performance/roc_forces.pdf", transparent=False)
        plt.close(fig)
        print("Saved plot: Figures/flight performance/roc_forces.pdf")

    def _plot_roc_power(self, V, DV, TV, V_stall):
        """Generates a styled Power Available vs. Power Required plot with a useful view."""
        _set_report_style()
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.plot(V, TV, label='Power Available', color=COLOR_PALETTE['green'])
        ax.plot(V, DV, label='Power Required', color=COLOR_PALETTE['blue'])
        ax.fill_between(V, TV, DV, where=(TV > DV), color=COLOR_PALETTE['green'], alpha=0.1, label='Excess Power')
        ax.axvline(x=V_stall, color=COLOR_PALETTE['red'], linestyle=':', linewidth=2, label=f'$V_{{stall}} = {V_stall:.1f}$ m/s')
        
        # --- Intelligent Cropping ---
        ax.set_ylim(bottom=0, top=np.max(TV) * 1.1)
        ax.set_xlim(left=0)
        
        #ax.set_title('Power vs. Airspeed')
        ax.set_xlabel('Velocity ($V_{EAS}$) [m/s]')
        ax.set_ylabel('Power [W]')
        ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='lightgrey')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        legend = ax.legend(loc='best', frameon=True)
        frame = legend.get_frame()
        frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
        frame.set_facecolor('white')
        frame.set_edgecolor('black')
        frame.set_alpha(0.8)
        legend.set_zorder(10)
        
        plt.tight_layout()
        os.makedirs("Figures", exist_ok=True)
        plt.savefig("Figures/flight performance/roc_power.pdf", transparent=False)
        plt.close(fig)
        print("Saved plot: Figures/flight performance/roc_power.pdf")

    def stall_speed(self, W, S, rho, CLmax):
        return ((W/S)*(2/rho)*(1/CLmax))**0.5
    
    def endurance(self, Wfuel, Wtotal, Cd0, AR, oswald, cT):
        CD = 2 * Cd0
        CL = (Cd0 * math.pi * oswald * AR)**0.5
        endurance = 1/(cT*0.000001*9.81) * CL/CD * math.log(Wtotal/(Wtotal-Wfuel))
        return endurance
    
    def performance_limit(self, W, S, CLmax, T0, cd0, A, oswald, plot=False):
        h = np.arange(0,20000,1)
        Vmin, Vmax, actual_h = [], [], []
        
        for val in h:
            _, _, density1, _ = __ISA__(val)
            Vstall = self.stall_speed(W, S, density1, CLmax)
            thrust = T0*(density1/1.225)
            V = np.arange(1, 500, 0.1)
            D, _, _ = self.__drag__(cd0, density1, V, S, W, A, oswald)
            
            # Find Vmax
            idx_vmax = np.where((D < thrust) & (V > Vstall))[0]
            if len(idx_vmax) == 0:
                hmax = val
                break
            Vmax.append(V[idx_vmax[-1]])
            
            # Find Vmin
            idx_vmin = np.where(D < thrust)[0]
            Vmin.append(max(Vstall, V[idx_vmin[0]]))
            actual_h.append(val)
        
        if plot:
            self._plot_performance_limit(Vmin, Vmax, actual_h)
        
        return (hmax, max(Vmax))

    def _plot_performance_limit(self, Vmin, Vmax, h):
        """Generates a styled flight envelope plot."""
        _set_report_style()
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.plot(Vmin, h, color=COLOR_PALETTE['blue'], label='Min Speed (Stall Limit)')
        ax.plot(Vmax, h, color=COLOR_PALETTE['grey'], label='Max Speed (Thrust Limit)')
        ax.fill_betweenx(h, Vmin, Vmax, color=COLOR_PALETTE['blue'], alpha=0.1, label='Flight Envelope')

        #ax.set_title('Flight Envelope')
        ax.set_xlabel('True Airspeed ($V_{TAS}$) [m/s]')
        ax.set_ylabel('Altitude ($h$) [m]')
        ax.grid(True, which='major', linestyle=':', linewidth=0.5, color='lightgrey')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)

        legend = ax.legend(loc='best', frameon=True)
        frame = legend.get_frame()
        frame.set_boxstyle('round,pad=0.5,rounding_size=0.4')
        frame.set_facecolor('white')
        frame.set_edgecolor('black')
        frame.set_alpha(0.8)
        legend.set_zorder(10)
        
        plt.tight_layout()
        os.makedirs("Figures", exist_ok=True)
        plt.savefig("Figures/flight performance/performance_limit.pdf", transparent=False)
        plt.close(fig)
        print("Saved plot: Figures/flight performance/performance_limit.pdf")

# ... (run_flight_performance and if __name__ == "__main__" remain the same) ...

if __name__ == "__main__":
    fp = FlightPerformance()

    # Initialize design parameters
    params = DesignParameters()
    params.load_from_yaml('design_config.yaml')

    # Set up parameters for flight performance calculations
    # ...
    print('tsfc1',params.engine.cruise_tsfc_SI)
    print('tsfc2',params.engine.take_off_tsfc)
    # Generate styled plots by calling the main methods with plot=True
    #fp.drag_plot(0.017, 0.3, np.arange(1,300, 1), 12, 4000*9.81, 12, 0.85, 60)
    #fp.drag_plot(params.wing.C_D0, )
    #fp.payload_range(14*(10**-6), 10, 0.88, 0.017, 35000, 12000, 15000, 0.3108, 15, True)
    print("T1", params.engine.engine_max_thrust)
    result1 = fp.payload_range(params.engine.cruise_tsfc_SI, params.wing.A_w_target, params.wing.e, params.wing.C_D0, params.weight.W_TO, params.weight.W_F - params.weight.W_F_res , params.weight.W_OE, 0.3108, params.wing.S_w, True)
    print('pl-range', result1)
    #fp.ROC(0.017, 1.225, np.arange(1,300,1), 15, 35000, 10, 0.85, 7000, 60, plot=True)
    result2 = fp.ROC(params.wing.C_D0, 1.225, np.arange(1,400,1), params.wing.S_w, params.weight.W_TO, params.wing.A_w_target, params.wing.e, params.engine.engine_max_thrust, fp.stall_speed(params.weight.W_TO, params.wing.S_w, 1.225, params.performance.CL_max_TO), plot=True)
    print('ROC',result2)
    #fp.performance_limit(35000, 15, 1.6, 7000, 0.017, 12, 0.88, True)
    result3 = fp.performance_limit(params.weight.W_TO, params.wing.S_w, params.performance.CL_max_TO, params.engine.engine_max_thrust, params.wing.C_D0, params.wing.A_w_target, params.wing.e, True)
    print('perf-limit', result3)
    
    result4= FlightSim().ground_run2(params.engine.engine_max_thrust, params.weight.W_TO/9.81, params.wing.S_w, params.wing.C_D0, params.wing.A_w_target, params.wing.e, params.engine.take_off_tsfc, params.performance.CL_max_TO, 1500)
    print('ground run', result4)
    result6=fp.stall_speed(params.weight.W_TO, params.wing.S_w, 1.225, params.performance.CL_max_TO)
    print('stall', result6)
    result5=fp.endurance(params.weight.W_F - params.weight.W_F_res, params.weight.W_TO, params.wing.C_D0, params.wing.A_w_target, params.wing.e, params.engine.cruise_tsfc_SI)
    print('endurance',result5)
    
    result7 = fp.__drag__(params.wing.C_D0, 0.3108, 250, params.wing.S_w, params.weight.W_TO, params.wing.A_w_target, params.wing.e, params.wing.CL)
    print('drag',result7)
    
    result8 = fp.__trim_drag__(0.3108,250, params.empennage.Vh_v, params.empennage.S_h, params.empennage.A_t_h, params.wing.e, params.empennage.CL_h)
    print('trim drag',result8)