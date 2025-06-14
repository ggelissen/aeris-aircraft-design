import math
import matplotlib.pyplot as plt
import numpy as np

from design_variables import DesignParameters
from subsystems.flightperformance.utils_flight import __ISA__
from subsystems.flightperformance.FlightSim import FlightSim
from subsystems.flightperformance.take_off_requirement import calculate_Cm
 
class FlightPerformance:
    def __init__(self):
        pass
    
    def __drag__(self, cd0, rho, V, S, W, A, oswald):
        '''
        weight in N!
        '''
        
        C_L = W/(0.5*rho*V**2*S)
        D0 = cd0 * 0.5 * rho * V**2 * S
        Di = (C_L**2)/(math.pi * A * oswald) * 0.5 * rho * V**2 * S
        D = D0 + Di
        
        return D, D0, Di
        
    
    def drag_plot(self, cd0, rho, V, S, W, A, oswald): # pragma: no cover
        
        D, D0, Di = self.__drag__(cd0, rho, V, S, W, A, oswald)
        
        plt.plot(V, D, label="Total Drag")
        plt.plot(V, D0, label="Zero-lift Drag")
        plt.ylim(0, max(D0))
        plt.plot(V, Di, label="Lift-induced Drag")
        plt.legend()
        plt.show()
    
    def __range__(self, cT, W_ini, W_fin, A, oswald, cd0, rho, S):
        '''
        weight in N!
        '''
        C_L = (0.3333333 * math.pi * A * oswald * cd0)**0.5
        C_D = 1.33333333333* cd0
        W = ((W_ini+W_fin)/2)/9.81
        Vopt = ( (2/rho) * (W/S) * (1/C_L) )**0.5
        
        R = Vopt/(9.81*cT)*C_L/C_D*math.log(W_ini/W_fin)
        
        return R/1000, Vopt

    def payload_range(self, cT, A, oswald, cd0, Wtotal, Wfuel, OEW, rho, S, plot=False):
        
        #range = self.__range__(V, cT, Wtotal, Wtotal-Wfuel, 12, 0.85, 0.017)
        #range2 = self.__range__(V, cT, Wtotal-100*9.81, Wtotal-Wfuel-100*9.81, 12, 0.85, 0.017)
        #print("range")
        #print(range, range2)
        #print("--")
        
        '''
        weight in N!
        '''
        
        Wpayload = np.arange(Wtotal-Wfuel-OEW, 0, -1*9.81)
        range = []
        for payload in Wpayload:
            range.append(self.__range__(cT, Wtotal - payload , Wtotal-Wfuel -payload ,A, oswald, cd0, rho, S)[0])
        
        
        if plot: # pragma: no cover
            plt.plot(range, (Wtotal-Wpayload)/9.81)
            plt.show()
        
        return (min(range), max(range))
        
    
    def ROC(self, cd0, rho, V, S, W, A, oswald, T, plot=False):
        
        '''
        V = numpy list! (np.arange(1,Vmax,1))
        '''
        
        D, D0, Di = self.__drag__(cd0, rho, V, S, W, A, oswald)
        
        
        
        AOC = (T - min(D)) / W
        AOC_V = V[np.argmin(D)]
        print(f"max angle of climb: {AOC} at V = {AOC_V}")
        
        if plot: # pragma: no cover
            plt.plot(V,D,label='drag')
            plt.plot(V,[T]*len(V),label='thrust')
            plt.ylim(0, T*1.1)
            plt.legend()
            plt.show()
        
        
        TV = V*T
        DV = D*V
        ROC = []
        for i in range(len(V)):
            val = V[i]
            ROC.append((T*val - D[i]*val) / (W))
        #print(max(ROC))
        #print(ROC)
        ROC_V = V[np.argmax(ROC)]
        print(f"max rate of climb: {max(ROC)} at V = {ROC_V}")
        
        if plot: # pragma: no cover
            plt.plot(V,DV,label='drag')
            plt.plot(V,TV,label='thrust')
            plt.ylim(0, max(TV)*1.1)
            plt.legend()
            plt.show()
        
        return AOC, AOC_V, max(ROC), ROC_V
        
    def stall_speed(self, W, S, rho, CLmax):
        return ((W/S)*(2/rho)*(1/CLmax))**0.5
    
    def endurance(self, Wfuel, Wtotal, Cd0, AR, oswald, cT):
        '''
        cT is kg/s/N
        output is endurance in seconds
        Weights in N
        '''
        k2 = (1/(math.pi*AR*oswald))
        CLopt = ((12*k2*Cd0)**0.5) / (2*k2)
        # Vopt = ((W/S)*(2/rho)*(1/CLopt))**0.5
        CD = Cd0 + ((CLopt)**2)*k2
        
        D = (CD/CLopt) * Wtotal
        
        FF = cT * D # kg/s
        
        
        endurance = Wfuel/9.81 / FF
        
        return endurance
    
    def performance_limit(self, W, S, CLmax, T0, cd0, A, oswald, plot=False):
        h = np.arange(0,20000,1)
        density = []
        Vmin = []
        T = []
        Vmax = []
        
    
        for val in h:
            _, _, density1, _ = __ISA__(val)
            density.append(density1)
            Vstall = self.stall_speed(W, S, density1, CLmax)
            #Vmin.append(Vmin1)
            thrust = T0*(density1/1.225)
            T.append(thrust)
            V = np.arange(1,500,0.1)
            D, D0, Di = self.__drag__(cd0, density1, V, S, W, A, oswald)
            # if val % 1000 == 0:
            #     print(val)
            #     plt.plot(V,D,label='drag')
            #     plt.plot(V,[thrust]*len(V),label='thrust')
            #     plt.ylim(0, thrust*1.1)
            #     plt.legend()
            #     plt.show()
            
            added = False
            for i in range(len(D)-1, 0, -1):
                drag = D[i]
                if drag < thrust and V[i] > Vstall:
                    Vmax1 = V[i]
                    Vmax.append(Vmax1)
                    added = True
                    break
                elif drag > thrust:
                    continue
            
            for i in range(0, len(D)-1, 1):
                drag = D[i]
                if drag < thrust:
                    Vmin1 = V[i]
                    break
                elif drag > thrust:
                    continue
            
            if added == False:
                hmax = val
                print(hmax)
                break
            
            Vmin_actual = max(Vstall, Vmin1)
            Vmin.append(Vmin_actual)
            
        actual_h = np.arange(0,hmax,1)
            
            
        if plot: # pragma: no cover
            plt.plot(Vmin, actual_h)
            plt.plot(Vmax, actual_h)
            plt.show()
        
        return (hmax, max(Vmax))
        


def run_flight_performance(params: DesignParameters): # pragma: no cover
    """
    Runs the control and stability analysis with the given design parameters.

    Parameters:
    params (DesignParameters): Design parameters for the aircraft.
    """
    # Initialize the Control class with parameters from DesignParameters
    fp = FlightPerformance()
    fs = FlightSim()
    Wfuel = params.weight.W_F
    cd0 = params.wing.C_D0
    AR = params.wing.A_w_target
    oswald = params.wing.e
    cT = params.engine.cruise_tsfc/3600
    Wtotal = params.weight.W_TO
    OEW = params.weight.W_OE
    S = params.wing.S_w
    CLmax_cruise = params.performance.CL_max_cruise
    CLmax_TO = params.performance.CL_max_TO
    T0 = params.engine.engine_max_thrust
    C_m_ac = params.fuselage.C_m_ac
    S_h = params.empennage.S_h
    l_h = params.empennage.L_h
    V_h_V = params.empennage.Vh_v
    x_cg = params.cg.cg_vector_from_3Dmodel
    x_w = params.cg.x_cg_wing
    c = params.wing.mac
    C_N_h = params.empennage.CL_h
    z_cg = params.cg.z_cg
    z_p = params.cg.z_cg_propulsion
    # Example usage of calculate_range method
    T, X, M = fs.ground_run2(T0,Wtotal/9.81,S,cd0,AR,oswald,cT*1000000,CLmax_TO)
    endurance = fp.endurance(Wfuel, Wtotal, cd0, AR, oswald, cT)
    min_range, max_range = fp.payload_range(params.cruise_speed, cT, AR, oswald, cd0, Wtotal, Wfuel, OEW)
    ceiling, vmax = fp.performance_limit(Wtotal, S, CLmax_cruise, T0, cd0, AR, oswald)
    stall_speed_cruise = fp.stall_speed(Wtotal, S, params.cruise_density, CLmax_cruise)
    stall_speed_takeoff = fp.stall_speed(Wtotal, S, 1.225, CLmax_TO)
    ROC_sea_level = fp.ROC(cd0, params.cruise_density, params.stall_speed_land, S, Wtotal, AR, oswald, T0)[2]
    take_off_requirement = calculate_Cm(C_m_ac, Wtotal/9.81, S, S_h, l_h, V_h_V, x_cg, x_w, c, C_N_h, z_cg, z_p, cd0, AR, oswald, cT*1000000, CLmax_TO)
    
    result = {
        "endurance [s]": endurance,
        "range with payload [km]": min_range,
        "range without payload [km]": max_range,
        "ceiling [m]": ceiling,
        "max speed [probably sealevel] [m/s]": vmax,
        "stall speed cruise [m/s]": stall_speed_cruise,
        "stall speed takeoff [m/s]": stall_speed_takeoff,
        "ROC at sea level [m/s]": ROC_sea_level,
        "take-off thrust [N]": T,
        "take-off distance (set value) [m]": X,
        "take-off speed [M]": M,
        "take-off req met? [bool]": take_off_requirement[1]
    }

    return result

        
        
if __name__ == "__main__": # pragma: no cover
    
    #FlightPerformance().drag_plot(0.017, 0.3, np.arange(1,300, 1), 12, 4000*9.81, 12, 0.85)
    
    #print(FlightPerformance().__range__(200, 0.00020, 4000*9.81, 3000*9.81, 12, 0.85, 0.017))
    
    #FlightPerformance().payload_range(200, 0.00020, 12, 0.85, 0.017, 4000*9.81, 2000*9.81, 1000*9.81)
    
    #FlightPerformance().ROC(0.017, 0.3, np.arange(1,300,1), 12, 4000*9.81, 12, 0.85, 2265)
    
    FlightPerformance().performance_limit(4000*9.81, 12, 1.5, 8000, 0.017, 12, 0.9)
        
        