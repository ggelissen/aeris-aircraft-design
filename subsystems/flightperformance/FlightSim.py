import math
import matplotlib.pyplot as plt

class FlightSim:
    def __init__(self):
        pass
    
    def __ISA__(self, altitude: float):
        T0 = 288.15
        L = 0.0065
        p0 = 101325
        g0 = 9.80665
        R = 287.05
        gamma = 1.4
        rho0 = 1.225
        
        if altitude < 0:
            T = 288.15
            p = p0
            rho = rho0
        elif altitude < 11000:
            T = T0 - L * altitude
            #p = (p0 * (T / T0)) ** (g0 / (L * R))
            p = p0 * (1 - L/T0*altitude)**(g0/(R*L))
            rho = rho0 * (1 - L/T0*altitude)**(g0/(R*L)-1)
        else:
            T = T0 - L * 11000
            #p11 = (p0 * (T / T0)) ** (g0 / (L * R))
            p11 = p0 * (1 - L/T0*11000)**(g0/(R*L))
            rho11 = rho0 * (1 - L/T0*11000)**(g0/(R*L)-1)
            print(p11, rho11)
            #p = p11 * math.exp(-g0 * (altitude - 11000) / (R * T))
            p = p11 * math.exp(-g0/(R*T)*(altitude-11000))
            rho = rho11 * math.exp(-g0/(R*T)*(altitude-11000))
        
        a = (gamma * R * T)**0.5
        #rho = p / (R * T)
        temperature = T
        pressure = p
        density = rho
        speed_of_sound = a
        
        return temperature,pressure,density,speed_of_sound
        
    def __plot_result__(self, x, y):
        plt.plot(x, y)
        plt.show()
    
    def level_flight(self, T: float, altitude: float):
        # constant
        _,_,density,speed_of_sound = self.__ISA__(altitude)
        print('sos', speed_of_sound)
        print('density',density)
        density = 0.311855
        TSFC = 20
        
        # FF(g/s) = TFSC(g/Kns) * T(kN)
        
        Cd = 0.04
        S = 4
        g0 = 9.80665
        
        
        
        # initial:
        mass = 3500
        W = mass * g0
        V = 0
        x = 0
        D = 1/2 * density * V * V * Cd * S
        
        C_L = 1.2 #W / (1/2 * density * V * V * S)
        L = W
        #T = 0
        EOM_X = T - D
        EOM_Y = L - W
        #L = W
        acc_X = EOM_X/mass
        acc_Y = EOM_Y/mass
        t = 0.0
        dt = 0.1
        
        V_history = []
        acc_history = []
        x_history = []
        t_history = []
        M_history = []
        mass_history = []
        alt_history = []
        # range -> V/FF = max
        V_Y= 0 
        
        
        
        while True:
            if (t >= 2000):
                break
            V_history.append(V)
            acc_history.append(acc_X)
            mass_history.append(mass)
            x_history.append(x)
            t_history.append(t)
            M_history.append(V/speed_of_sound)
            alt_history.append(altitude)
            V += acc_X * dt
            x += V * dt
            D = 1/2 * density * V * V * Cd * S
            FF = TSFC * T / 1000
            mass -= (FF * dt / 1000)
            W = mass * g0
            
            L = C_L * 1/2 * density * V * V  * S
            
            acc_Y = (L - W) / mass
            V_Y += acc_Y *dt
            altitude += V_Y * dt
            
            
            #print(V)
            #print(speed_of_sound)
            #print('D',D)
            #print('T',T)
            EOM_X = T - D
            #print('EOM',EOM)
            acc_X = EOM_X/mass
            #print('acc',acc)
            t += dt
        
        self.__plot_result__(t_history, V_history)
        self.__plot_result__(t_history, M_history)
        self.__plot_result__(t_history, mass_history)
        self.__plot_result__(t_history, alt_history)
        #print(t_history)
        #print(V_history)
        
    def climb_flight(self, T, altitude):
        _,_,density,speed_of_sound = self.__ISA__(altitude)
        print('sos', speed_of_sound)
        print('density',density)
        density = 0.311855
        
        Cd = 0.04
        S = 4
        # initial:
        mass = 3500
        V = 0
        x = 0
        D = 1/2 * density * V * V * Cd * S
        EOM = T - D 
        acc = EOM/mass
        t = 0.0
        dt = 0.1
        M = V / speed_of_sound
        
        V_history = []
        acc_history = []
        x_history = []
        t_history = []
        M_history = []
        
        while True:
            if (t >= 1000):
                break
            V_history.append(V)
            acc_history.append(acc)
            x_history.append(x)
            t_history.append(t)
            M_history.append(V/speed_of_sound)
            V += acc * dt
            x += V * dt
            D = 1/2 * density * V * V * Cd * S
            
            #print(V)
            #print(speed_of_sound)
            #print('D',D)
            #print('T',T)
            EOM = T - D
            #print('EOM',EOM)
            acc = EOM/mass
            #print('acc',acc)
            t += dt
        
        self.__plot_result__(t_history, V_history)
        self.__plot_result__(t_history, M_history)
        #print(t_history)
        #print(V_history)
        
        

if __name__ == "__main__":
    FlightSim().level_flight(2000, 12000)
        