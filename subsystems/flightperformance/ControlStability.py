import matplotlib.pyplot as plt
import numpy as np

class Control:
    def __init__(self, CLah, CLaA_h, de_da, lh, mac, Vh_V, x_ac, CLh, CLA_h, C_m_ac):
        self.CLah = CLah
        self.CLaA_h = CLaA_h
        self.de_da = de_da
        self.lh = lh
        self.mac = mac
        self.Vh_V = Vh_V
        #x_cg = 5
        self.x_ac = x_ac
        self.CLh = CLh
        self.CLA_h = CLA_h
        self.C_m_ac = C_m_ac
        self.X = np.arange(0,1,0.01)
        
        
    def __plot_result__(self, x, y, legend, x_label="x", y_label='y',y_limit = [None, None]):
        for i in range(len(x)):  
            plt.plot(x[i], y[i], label=legend[i])
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.ylim(y_limit[0],y_limit[1])
        plt.legend()
        plt.show()
    
    def __stability_curve__(self, X, plot=False):
        
        den = (self.CLah/self.CLaA_h)*(1-self.de_da)*self.lh/self.mac*((self.Vh_V)**2)
        #print(den)
        Y = 1/(den)*X-((self.x_ac-0.05)/(den))
        
        if plot:
            self.__plot_result__(X, Y, "xcg/mac", "Sh/S")
        
        return Y
    
    def __control_curve__(self, X, plot=False):
        den = self.CLh/self.CLA_h*self.lh/self.mac*(self.Vh_V**2)
        Y = (1/den*X)+((self.C_m_ac/self.CLA_h)-self.x_ac)/(den)
        
        if plot:
            self.__plot_result__(X, Y, "xcg/mac", "Sh/S")

        return Y

    def __calculate_X_stability__(self, Y):
        den = (self.CLah/self.CLaA_h)*(1-self.de_da)*self.lh/self.mac*((self.Vh_V)**2)
        X = (Y+((self.x_ac-0.05)/(den))) * den 
        return X
        
        
    def scissor_plot(self, plot=False):
        
        stability = self.__stability_curve__(self.X)
        controllability = self.__control_curve__(self.X)
        if plot:
            self.__plot_result__([self.X,self.X], [stability, controllability],y_limit=[0,None],y_label="Sh/S",x_label="xcg/mac",legend=["stability", "controllability"])
        
        return stability, controllability
        
    def xcg_OEW_estimation(self, W_wing, X_wing, W_fuselage, X_fuselage):
        
        return ((W_wing*X_wing + W_fuselage*X_fuselage) / (W_wing + W_fuselage))
    
    def cg_range(self, W_OEW, X_OEW, W_payload, X_payload, W_fuel, X_fuel): 
        Xcg = X_OEW
        Wcg = W_OEW
        for i in np.arange(len(W_payload)):
            if X_payload[i] > X_OEW:
                Xcg = (Xcg*Wcg + X_payload[i]*W_payload[i])/(Wcg+W_payload[i])
                Wcg = Wcg+W_payload[i]
            max1 = Xcg
        Xcg = X_OEW
        Wcg = W_OEW
        for i in np.arange(len(W_payload)):
            if X_payload[i] < X_OEW:
                Xcg = (Xcg*Wcg + X_payload[i]*W_payload[i])/(Wcg+W_payload[i])
                Wcg = Wcg+W_payload[i]
            min1 = Xcg
        
        for i in np.arange(len(W_payload)):
            Xcg = (Xcg*Wcg + X_payload[i]*W_payload[i])/(Wcg+W_payload[i])
            Wcg = Wcg+W_payload[i]
        
        
        for i in np.arange(len(W_fuel)):
            if X_fuel[i] > X_OEW:
                Xcg = (Xcg*Wcg + X_fuel[i]*W_fuel[i])/(Wcg+W_fuel[i])
                Wcg = Wcg+W_fuel[i]
            max2 = Xcg
        
        for i in np.arange(len(W_payload)):
            Xcg = (Xcg*Wcg + X_payload[i]*W_payload[i])/(Wcg+W_payload[i])
            Wcg = Wcg+W_payload[i]
        
        for i in np.arange(len(W_fuel)):
            if X_fuel[i] < X_OEW:
                Xcg = (Xcg*Wcg + X_fuel[i]*W_fuel[i])/(Wcg+W_fuel[i])
                Wcg = Wcg+W_fuel[i]
            min2 = Xcg
        
        if abs(max2) > abs(max1):
            max_cg = max2*1.02
        else:
            max_cg = max1*1.02
        
        if abs(min2) > abs(min1):
            min_cg = min2*0.98
        else:
            min_cg = min1*0.98
        
        return (min_cg, max_cg)
    

    def __overlay_graphs__(self, X, Y1, Y2, stability, controllability, Sh, x_lemac):
        fig, ax1 = plt.subplots()

        ax1.set_xlabel('xcg/mac')
        ax1.set_ylabel('x_lemac/lh')
        ax1.plot(Y1, X, label="min", color ='tab:green')
        ax1.plot(Y2, X, label="max", color = 'tab:red')
        #l, b, w, h = ax1.get_position().bounds
        #ax1.set_position([l, b, w*0.5, h])
        ax1.set_ylim(x_lemac*0.9,x_lemac*1.1)
        
        ax2 = ax1.twinx()
        
        ax2.set_ylabel('Sh/S')  # we already handled the x-label with ax1
        ax2.plot(X, stability, label="stability")
        ax2.plot(X, controllability, label="controllability")
        ax2.plot(X, len(X)*[Sh], label="Sh/S", color="tab:pink")
        ax2.set_ylim(0,None)
    

        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        fig.legend()
        plt.show()
        
    def calculate_range(self, W_OEW, W_payload, X_payload, W_fuel, W_wing, W_fuselage, X_fuselage):
        stability, controllability = control.scissor_plot(False)
    
        Y1 = []
        Y2 = []
        for i in self.X:    
            result = control.cg_range(W_OEW, self.xcg_OEW_estimation(W_wing, i, W_fuselage, X_fuselage), W_payload, X_payload, W_fuel, [i])
            Y1.append(result[0])
            Y2.append(result[1])
        
        #control.__plot_result__([Y1, Y2], [control.X, control.X],["min","max"], "x_cg","x_lemac/lh")
        
        #print(stability)
        #print(controllability)
        for i in range(len(Y1)):
            Sh_S = self.__control_curve__(Y1[i])
            X_stability = self.__calculate_X_stability__(Sh_S)
            if (X_stability - Y1[i]) > (Y2[i] - Y1[i]):
                continue
            else:
                print('cg range',Y2[i] - Y1[i])
                print("Sh/S", Sh_S)
                x_lemac = control.X[i]
                print("x_lemac/lh",x_lemac)
                break
            
        control.__overlay_graphs__(control.X, Y1, Y2, stability, controllability, Sh_S, x_lemac)

        

if __name__ == "__main__":
    #Control().__stability_curve__()
    #Control().__control_curve__()
    control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, lh=5, mac=1, Vh_V=1, x_ac=0.4, CLh=-1, CLA_h=1, C_m_ac=-0.5)
    control.calculate_range(2000, [600], [0.3], [1000], 1000, 1000, 0.5)
    
    '''
    control = Control(CLah=0.1, CLaA_h=0.1, de_da=0.1, lh=5, mac=1, Vh_V=1, x_ac=0.4, CLh=-1, CLA_h=1, C_m_ac=-0.5)
    stability, controllability = control.scissor_plot(True)
    
    
    Y1 = []
    Y2 = []
    for i in control.X:    
        result = control.cg_range(2000, control.xcg_OEW_estimation(1000, i, 1000, 0.5), [600], [0.3], [1000], [i])
        Y1.append(result[0])
        Y2.append(result[1])
    
    #control.__plot_result__([Y1, Y2], [control.X, control.X],["min","max"], "x_cg","x_lemac/lh")
    
    #print(stability)
    #print(controllability)
    for i in range(len(Y1)):
        Sh_S = control.__control_curve__(Y1[i])
        X_stability = control.__calculate_X_stability__(Sh_S)
        if (X_stability - Y1[i]) > (Y2[i] - Y1[i]):
            continue
        else:
            print('cg range',Y2[i] - Y1[i])
            print("Sh/S", Sh_S)
            print("x_lemac/lh",control.X[i])
            break
        
    control.__overlay_graphs__(control.X, Y1, Y2, stability, controllability, Sh_S)
    '''
            
    
        
        
        
    
    
    #print(control.cg_range(2000, 0.5, [400,200], [0.2,0.7], [800,200], [0.5,0.25]))