import math
import matplotlib.pyplot as plt
import numpy as np
 
class FlightPerformance:
    def __init__(self):
        pass
    
    def __drag__(self, cd0, rho, V, S, W, A, oswald):
        
        C_L = W/(0.5*rho*V**2*S)
        D0 = cd0 * 0.5 * rho * V**2 * S
        Di = (C_L**2)/(math.pi * A * oswald) * 0.5 * rho * V**2 * S
        D = D0 + Di
        
        return D, D0, Di
        
    
    def drag_plot(self, cd0, rho, V, S, W, A, oswald):
        
        D, D0, Di = self.__drag__(cd0, rho, V, S, W, A, oswald)
        
        plt.plot(V, D, label="Total Drag")
        plt.plot(V, D0, label="Zero-lift Drag")
        plt.ylim(0, max(D0))
        plt.plot(V, Di, label="Lift-induced Drag")
        plt.legend()
        plt.show()
    
    def __range__(self, V,cT,W_ini,W_fin, A, oswald, cd0):
        C_L = (0.3333333 * math.pi * A * oswald * cd0)
        C_D = 1.33333333333* cd0
        
        R = V/cT*C_L/C_D*math.log(W_ini/W_fin)
        
        return R/1000

    def payload_range(self, V, cT, A, oswald, cd0, Wtotal, Wfuel, OEW):
        
        #range = self.__range__(V, cT, Wtotal, Wtotal-Wfuel, 12, 0.85, 0.017)
        #range2 = self.__range__(V, cT, Wtotal-100*9.81, Wtotal-Wfuel-100*9.81, 12, 0.85, 0.017)
        #print("range")
        #print(range, range2)
        #print("--")
        
        Wpayload = np.arange(Wtotal-Wfuel-OEW, 0, -1*9.81)
        range = []
        for payload in Wpayload:
            range.append(self.__range__(V, cT, Wtotal - payload , Wtotal-Wfuel -payload ,A, oswald, cd0))
        
        
        
        plt.plot(range, (Wtotal-Wpayload)/9.81)
        plt.show()
        
    
    def ROC(self, cd0, rho, V, S, W, A, oswald, T):
        
        D, D0, Di = self.__drag__(cd0, rho, V, S, W, A, oswald)
        
        
        
        AOC = (T - min(D)) / W
        
        print(f"max angle of climb: {AOC} at V = {V[np.argmin(D)]}")
        
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
        
        print(f"max rate of climb: {max(ROC)} at V = {V[np.argmax(ROC)]}")
        
        plt.plot(V,DV,label='drag')
        plt.plot(V,TV,label='thrust')
        plt.ylim(0, max(TV)*1.1)
        plt.legend()
        plt.show()
        
        
if __name__ == "__main__":
    
    #FlightPerformance().drag_plot(0.017, 0.3, np.arange(1,300, 1), 12, 4000*9.81, 12, 0.85)
    
    #print(FlightPerformance().__range__(200, 0.00020, 4000*9.81, 3000*9.81, 12, 0.85, 0.017))
    
    #FlightPerformance().payload_range(200, 0.00020, 12, 0.85, 0.017, 4000*9.81, 2000*9.81, 1000*9.81)
    
    FlightPerformance().ROC(0.017, 0.3, np.arange(1,300,1), 12, 4000*9.81, 12, 0.85, 2265)
        
        