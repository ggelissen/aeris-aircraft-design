import matplotlib.pyplot as plt
import numpy as np

from design_variables import DesignParameters

class Control:
    """
    A class to perform aircraft control and stability analysis, including generating scissor plots and calculating CG range.
    """
    def __init__(self, CLah, CLaA_h, de_da, mac, Vh_V, x_lemac, CLh, CLA_h, C_m_ac, l_fus):
        """
        Initializes the Control class with aerodynamic and geometric parameters.

        Parameters:
        CLah (float): Lift coefficient slope of the horizontal tail.
        CLaA_h (float): Lift coefficient slope of the aircraft less tail.
        de_da (float): Downwash effect on the lift coefficient.
        mac (float): Mean aerodynamic chord.
        Vh_V (float): Ratio of tail speed to free stream speed.
        x_ac (float): Aerodynamic center of the aircraft.
        CLh (float): Lift coefficient of the horizontal tail.
        CLA_h (float): Lift coefficient of the aircraft less tail (used in controllability).
        C_m_ac (float): Moment coefficient at the aerodynamic center.
        l_fus (float): Length of fuselage [m]
        """
        self.CLah = CLah
        self.CLaA_h = CLaA_h
        self.de_da = de_da
        self.mac = mac
        self.Vh_V = Vh_V
        self.x_lemac = x_lemac
        self.x_ac = x_lemac + mac / 4
        self.lh = l_fus - self.x_ac
        self.CLh = CLh
        self.CLA_h = CLA_h
        self.C_m_ac = C_m_ac
        self.x_lemac_lfus = 1
        self.l_fus = l_fus
        # Define a range for xcg/mac for plotting
        self.cg_list = np.arange(0, 1, 0.001)
        self.x_lemac_lfus_list = np.arange(0,1, 0.001)

    def __plot_result__(self, x, y, legend, x_label="x", y_label='y', y_limit=[None, None]): # pragma: no cover
        """
        Plots a given set of data with labels and legend.

        Parameters:
        x (list): List of x-data arrays.
        y (list): List of y-data arrays.
        legend (list): List of legend labels for each data set.
        x_label (str): Label for the x-axis.
        y_label (str): Label for the y-axis.
        y_limit (list): List containing the lower and upper limits for the y-axis.
        """
        for i in range(len(x)):
            plt.plot(x[i], y[i], label=legend[i])
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.ylim(y_limit[0], y_limit[1])
        plt.legend()
        plt.show()
            
    def __normalise_coordinate__(self, x, lemac):
        return (x - lemac) / self.mac

    def __stability_curve__(self, X, plot=False):
        """
        Calculates the stability curve for the scissor plot.

        Parameters:
        X (np.ndarray): Array of xcg/mac values.
        plot (bool): Whether to plot the stability curve.

        Returns:
        np.ndarray: Array of Sh/S values for the stability curve.
        """
        # Calculate the denominator term for the stability equation
        den = (self.CLah / self.CLaA_h) * (1 - self.de_da) * self.lh / self.mac * ((self.Vh_V)**2)
        # Calculate the stability curve (Sh/S vs xcg/mac)
        Y = (1 / den) * X - ((self.__normalise_coordinate__(self.x_ac, self.x_lemac) - 0.05) / den) # Assuming a stability margin of 0.05
        #print('stability',Y)
        #print('stab den',den)
        if plot: # pragma: no cover
            self.__plot_result__([X], [Y], ["Stability"], "xcg/mac", "Sh/S")

        return Y

    def __control_curve__(self, X, plot=False):
        """
        Calculates the controllability curve for the scissor plot.

        Parameters:
        X (np.ndarray): Array of xcg/mac values.
        plot (bool): Whether to plot the controllability curve.

        Returns:
        np.ndarray: Array of Sh/S values for the controllability curve.
        """
        # Calculate the denominator term for the controllability equation
        den = self.CLh / self.CLA_h * self.lh / self.mac * (self.Vh_V**2)
        # Calculate the controllability curve (Sh/S vs xcg/mac)
        Y = (1 / den) * X + ((self.C_m_ac / self.CLA_h) - self.__normalise_coordinate__(self.x_ac, self.x_lemac)) / den

        if plot: # pragma: no cover
            self.__plot_result__([X], [Y], ["Controllability"], "xcg/mac", "Sh/S")

        return Y

    def __calculate_X_stability__(self, Y):
        """
        Calculates the xcg/mac value on the stability curve for a given Sh/S.

        Parameters:
        Y (float): Sh/S value.

        Returns:
        float: xcg/mac value on the stability curve.
        """
        den = (self.CLah / self.CLaA_h) * (1 - self.de_da) * self.lh / self.mac * ((self.Vh_V)**2)
        X = (Y + ((self.__normalise_coordinate__(self.x_ac, self.x_lemac) - 0.05) / den)) * den
        return X

    def scissor_plot(self, plot=False):
        """
        Generates the stability and controllability curves for the scissor plot.

        Parameters:
        plot (bool): Whether to plot the scissor plot.

        Returns:
        tuple: Arrays of Sh/S values for the stability and controllability curves.
        """
        stability = self.__stability_curve__(self.cg_list)
        controllability = self.__control_curve__(self.cg_list)
        if plot: # pragma: no cover
            self.__plot_result__([self.cg_list, self.cg_list], [stability, controllability], y_limit=[0, None], y_label="Sh/S", x_label="xcg/mac", legend=["Stability", "Controllability"])

        return stability, controllability

    def xcg_OEW_estimation(self, W_wing, X_wing, W_fuselage, X_fuselage):
        """
        Estimates the xcg for the Operational Empty Weight (OEW).

        Parameters:
        W_wing (float): Weight of the wing.
        X_wing (float): x-location of the wing CG.
        W_fuselage (float): Weight of the fuselage.
        X_fuselage (float): x-location of the fuselage CG.

        Returns:
        float: Estimated xcg for OEW.
        """
        return ((W_wing * X_wing + W_fuselage * X_fuselage) / (W_wing + W_fuselage))

    def cg_range(self, W_OEW, X_OEW, W_payload, X_payload, W_fuel, X_fuel):
        """
        Calculates the center of gravity (CG) range for different loading conditions.

        Parameters:
        W_OEW (float): Operational Empty Weight.
        X_OEW (float): x-location of the OEW CG.
        W_payload (list): List of payload weights.
        X_payload (list): List of x-locations for each payload item.
        W_fuel (list): List of fuel weights.
        X_fuel (list): List of x-locations for each fuel tank.

        Returns:
        tuple: Minimum and maximum xcg values.
        """
        # Calculate CG with payload added forward and aft of OEW
        Xcg_payload_fwd = X_OEW
        Wcg_payload_fwd = W_OEW
        Xcg_payload_aft = X_OEW
        Wcg_payload_aft = W_OEW
        Xcg_payload = X_OEW
        Wcg_payload = W_OEW

        for i in range(len(W_payload)):
            if X_payload[i] < X_OEW:
                Xcg_payload_fwd = (Xcg_payload_fwd * Wcg_payload_fwd + X_payload[i] * W_payload[i]) / (Wcg_payload_fwd + W_payload[i])
                Wcg_payload_fwd += W_payload[i]
            else:
                Xcg_payload_aft = (Xcg_payload_aft * Wcg_payload_aft + X_payload[i] * W_payload[i]) / (Wcg_payload_aft + W_payload[i])
                Wcg_payload_aft += W_payload[i]

        for i in range(len(W_payload)):
            Xcg_payload = (Xcg_payload * Wcg_payload + X_payload[i] * W_payload[i]) / (Wcg_payload + W_payload[i])
            Wcg_payload += W_payload[i]
        #print(Xcg_payload)
        # Calculate CG with fuel added forward and aft of OEW
        Xcg_fuel_fwd = Xcg_payload
        Wcg_fuel_fwd = Wcg_payload
        Xcg_fuel_aft = Xcg_payload
        Wcg_fuel_aft = Wcg_payload

        for i in range(len(W_fuel)):
            if X_fuel[i] < Xcg_payload:
                Xcg_fuel_fwd = (Xcg_fuel_fwd * Wcg_fuel_fwd + X_fuel[i] * W_fuel[i]) / (Wcg_fuel_fwd + W_fuel[i])
                Wcg_fuel_fwd += W_fuel[i]
            else:
                Xcg_fuel_aft = (Xcg_fuel_aft * Wcg_fuel_aft + X_fuel[i] * W_fuel[i]) / (Wcg_fuel_aft + W_fuel[i])
                #print('fuel_aft',Xcg_fuel_aft)
                Wcg_fuel_aft += W_fuel[i]

        # Determine the overall min and max CG
        min_cg = min(Xcg_payload_fwd, Xcg_fuel_fwd)
        max_cg = max(Xcg_payload_aft, Xcg_fuel_aft)

        # Apply a small margin (adjust as needed)
        min_cg *= 0.98
        max_cg *= 1.02

        return (min_cg, max_cg)

    def __overlay_graphs__(self, X, Y1, Y2, stability, controllability, Sh, x_lemac): # pragma: no cover
        """
        Overlays the CG range and scissor plot on a single graph.

        Parameters:
        X (np.ndarray): Array of xcg/mac values.
        Y1 (list): List of minimum CG values.
        Y2 (list): List of maximum CG values.
        stability (np.ndarray): Array of Sh/S values for the stability curve.
        controllability (np.ndarray): Array of Sh/S values for the controllability curve.
        Sh (float): Horizontal tail surface area.
        x_lemac (float): x-location of the wing leading edge mean aerodynamic chord.
        """
        fig, ax1 = plt.subplots()

        ax1.set_xlabel('xcg/mac')
        ax1.set_ylabel('x_lemac/lh') # This label seems incorrect based on the plot data
        ax1.plot(Y1, X, label="min", color='tab:green')
        ax1.plot(Y2, X, label="max", color='tab:red')
        #l, b, w, h = ax1.get_position().bounds
        #ax1.set_position([l, b, w*0.5, h])
        # The y-limit here seems to be trying to focus on a single x_lemac value, which might not be intended
        ax1.set_ylim(x_lemac * 0.99999, x_lemac * 1.00001)

        ax2 = ax1.twinx()

        ax2.set_ylabel('Sh/S')  # we already handled the x-label with ax1
        ax2.plot(X, stability, label="stability")
        ax2.plot(X, controllability, label="controllability")
        # Plot a horizontal line for the calculated Sh/S
        ax2.plot(X, len(X) * [Sh], label="Sh/S", color="tab:pink")
        ax2.set_ylim(0, None)

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        fig.legend()
        plt.show()
        
    def __cg_range__plot__(self, W_wing, W_fuselage, X_fuselage, W_OEW, W_payload, X_payload, W_fuel):
        Y1 = [] # List to store minimum CG values
        Y2 = [] # List to store maximum CG values
        # Calculate CG range for different x_lemac/lh values
        for i in self.x_lemac_lfus_list:
            # Estimate OEW CG based on wing and fuselage weights and locations
            x_oew = self.xcg_OEW_estimation(W_wing, i*self.l_fus + self.mac/4, W_fuselage, X_fuselage)
            # Calculate the CG range for the current OEW CG
            result = self.cg_range(W_OEW, x_oew, W_payload, X_payload, W_fuel, [i*self.l_fus + self.mac/4]) # Assuming fuel is at x_lemac
            #print(i, x_oew, result[0], result[1], self.__normalise_coordinate__(result[0], i*self.l_fus), self.__normalise_coordinate__(result[1], i*self.l_fus))
            Y1.append(self.__normalise_coordinate__(result[0], i*self.l_fus))
            Y2.append(self.__normalise_coordinate__(result[1], i*self.l_fus))
        
        plt.plot(Y1, self.x_lemac_lfus_list, label="min")
        plt.plot(Y2, self.x_lemac_lfus_list, label="max")
        plt.legend()
        plt.show()
        

    def calculate_range(self, W_OEW, W_payload, X_payload, W_fuel, W_wing, W_fuselage, X_fuselage, plot=False):
        """
        Calculates the required Sh/S and x_lemac/lh for a given CG range to fit within the stability and controllability requirements.

        Parameters:
        W_OEW (float): Operational Empty Weight.
        W_payload (list): List of payload weights.
        X_payload (list): List of x-locations for each payload item.
        W_fuel (list): List of fuel weights.
        W_wing (float): Weight of the wing.
        W_fuselage (float): Weight of the fuselage.
        X_fuselage (float): x-location of the fuselage CG.
        """
        # Get stability and controllability curves
        stability, controllability = self.scissor_plot(False)

        Y1 = [] # List to store minimum CG values
        Y2 = [] # List to store maximum CG values
        # Calculate CG range for different x_lemac/lh values
        for i in self.x_lemac_lfus_list:
            # Estimate OEW CG based on wing and fuselage weights and locations
            x_oew = self.xcg_OEW_estimation(W_wing, i*self.l_fus + self.mac/4, W_fuselage, X_fuselage)
            # Calculate the CG range for the current OEW CG
            result = self.cg_range(W_OEW, x_oew, W_payload, X_payload, W_fuel, [i*self.l_fus + self.mac/4]) # Assuming fuel is at x_lemac
            Y1.append(self.__normalise_coordinate__(result[0], i*self.l_fus))
            Y2.append(self.__normalise_coordinate__(result[1], i*self.l_fus))


        # Find the intersection of the CG range with the stability and controllability requirements
        Sh_S = None
        # if plot:
        #     print("Y1", Y1, "Y2", Y2)
        for i in range(len(Y1)):
            # Calculate the required Sh/S for controllability at the minimum CG
            required_Sh_S_controllability = self.__control_curve__(Y1[i])
            # print('SH',required_Sh_S_controllability)
            # Calculate the xcg/mac on the stability curve for this Sh/S
            xcg_stability = self.__calculate_X_stability__(required_Sh_S_controllability)
            # print('xcg',xcg_stability)
            # print('Y1',Y1[i])
            # print('Ý2',Y2[i])
            # print('cond',(xcg_stability - Y1[i]), (Y2[i] - Y1[i]))
            # Check if the CG range is within the stable and controllable region
            if (xcg_stability - Y1[i]) < 0 or (xcg_stability - Y1[i]) < (Y2[i] - Y1[i]) or required_Sh_S_controllability < 0:
                # If the stability point is aft of the max CG, the range is not fully stable/controllable
                # print("continue")
                continue
            else:
                # Found a suitable Sh/S and x_lemac/lh
                Sh_S = required_Sh_S_controllability
                self.x_lemac_lfus = self.x_lemac_lfus_list[i]
                # print("suitable")
                # print('range', Y2[i] - Y1[i])
                # print('ShS',Sh_S)
                result = {
                    "cg_range": Y2[i] - Y1[i],
                    "Sh/S": Sh_S,
                    "x_lemac/lfus": self.x_lemac_lfus
                }
                #print('Y1',Y1, "Y2",Y2)
                break

        # Overlay the graphs if a solution was found
        if Sh_S is not None and self.x_lemac_lfus is not None:
            if plot == True: # pragma: no cover
                self.__overlay_graphs__(self.x_lemac_lfus_list, Y1, Y2, stability, controllability, Sh_S, self.x_lemac_lfus)
        else:
            print("No suitable Sh/S and x_lemac/lfus found for the given parameters.")
            return None

        return result


    def scissor_loop(self, OEW, Wpayload, Xpayload, Wfuel, Wwing, Wfuselage, Xfuselage):
        i = 0 
        while True:
            old_xlemac_fus = self.x_lemac_lfus
            print(self.lh)
            result = self.calculate_range(OEW, Wpayload, Xpayload, Wfuel, Wwing, Wfuselage, Xfuselage, False)
            
            self.x_lemac = self.x_lemac_lfus * self.l_fus
            self.x_ac = (self.x_lemac + self.mac/4)
            self.lh = self.l_fus - self.x_ac
            #print('x_lemac_fus',self.x_lemac_lfus)
            #print('old xlemac fus', old_xlemac_fus)
            if i == 20:
                break
            i += 1

        
            # self.x_lemac_lfus = result["x_lemac/lfus"]
            # self.x_lemac = self.x_lemac_lfus * self.l_fus
            # old_xac = self.x_ac
            # self.x_ac = (self.x_lemac + self.mac/4)
            # self.lh += old_xac - self.x_ac
            
            # print('x_lemac_fus',self.x_lemac_lfus)
            # print('lh',self.lh)
            
            # if abs(self.x_ac - old_xac) < 0.01:
            #     break
        
        #self.scissor_plot(True)
        #self.calculate_range(OEW, Wpayload, Xpayload, Wfuel, Wwing, Wfuselage, Xfuselage, False)
        return self.x_ac, result["Sh/S"], self.x_lemac_lfus, self.lh
            
        


def run_control_stability(params: DesignParameters): # pragma: no cover
    """
    Runs the control and stability analysis with the given design parameters.

    Parameters:
    params (DesignParameters): Design parameters for the aircraft.
    """
    # Initialize the Control class with parameters from DesignParameters
    control = Control(
        CLah=params.empennage.Cl_alpha,
        CLaA_h=params.wing.airfoil_clalpha,
        de_da=params.wing.de_da,
        lh=params.fuselage.lh,
        mac=params.wing.mac,
        Vh_V=params.empennage.Vh_v,
        x_ac=params.fuselage.x_ac,
        CLh=params.empennage.CL_h,
        CLA_h=params.wing.CL,
        C_m_ac=params.fuselage.C_m_ac
    )
    
    # Example usage of calculate_range method
    results = control.calculate_range(
        W_OEW=params.weight.W_OE,
        W_payload=params.weight.W_PL,
        X_payload=params.fuselage.x_payload,
        W_fuel=params.weight.W_F,
        W_wing=params.weight.W_wing,
        W_fuselage=params.weight.W_fus,
        X_fuselage=params.fuselage.x_fuselage
    )

    return results


if __name__ == "__main__": # pragma: no cover
    # Example usage
    # Initialize the Control class with example parameters
    #control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, lh=5, mac=2, Vh_V=1, x_ac=0.55, CLh=-2, CLA_h=0.6, C_m_ac=-0.5)
    # Calculate and plot the range
    #control.calculate_range(W_OEW=2000, W_payload=[600], X_payload=[0.3], W_fuel=[1000], W_wing=1000, W_fuselage=1000, X_fuselage=0.7)
    
    #control.cg_range(2500, 0.65, [100, 500], [0.8, 0.1], [800, 200], [0.65, 0.8])

    # Example of plotting scissor plot separately
    control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, mac=1, Vh_V=1, x_lemac=6, CLh=-1, CLA_h=1, C_m_ac=-0.5, l_fus=12)
    #stability, controllability = control.scissor_plot(True)
    result = control.scissor_loop(OEW=2000, Wpayload=[600], Xpayload=[4], Wfuel=[1000], Wwing=1000, Wfuselage=1000, Xfuselage=6)
    #control.calculate_range(W_OEW=2000, W_payload=[600], X_payload=[3], W_fuel=[1000], W_wing=1000, W_fuselage=1000, X_fuselage=7, plot=True)
    print(result)

    #control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, mac=1, Vh_V=1, x_lemac=7, CLh=-1, CLA_h=1, C_m_ac=-0.5, l_fus=12)
    #control.__cg_range__plot__(1000, 1000, 7, 2000, [600], [7], [1000])
    
    # Example of calculating CG range separately
    # control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, lh=5, mac=1, Vh_V=1, x_ac=0.4, CLh=-1, CLA_h=1, C_m_ac=-0.5)
    # print(control.cg_range(W_OEW=2000, X_OEW=0.5, W_payload=[400, 200], X_payload=[0.2, 0.7], W_fuel=[800, 200], X_fuel=[0.5, 0.25]))