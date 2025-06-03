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
            #print(p11, rho11)
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
        
    def __plot_result__(self, x, y, x_label, y_label):
        plt.plot(x, y)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.show()
    
    def __sign__(self, x: float):
        if x < 0:
            return -1
        else:
            return 1
    
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
        Cd0 = 0.0145 #Roskam, bizjet
        A = 9.0
        e = 0.85
        C_L_opt = (1/3 * math.pi * A * e * Cd0)**0.5
        C_D_opt = 4/3 * Cd0
        
        print('CL/CD',C_L_opt/C_D_opt)
        
        T_start = (C_D_opt/C_L_opt)*3150*9.80665
        T_avg = (C_D_opt/C_L_opt)*(3150*9.80665 - 0.5*10580)
        T_end = (C_D_opt/C_L_opt)*(3150*9.80665 - 10580)
        print("T",T_start)
        print("T",T_avg)
        print("T",T_end)
        
        
        
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
        
    def ground_run(self, T0):
        
        _,_,density,sos = self.__ISA__(0) # sea level
        
        mass = 3500
        g0 = 9.80665
        W = mass * g0
        V = 0 
        S = 12
        friction = 0.014
        Cd0 = 0.0145
        AR = 9.0
        oswald = 0.85
        t = 0
        dt = 0.001
        X = 0
        TSFC = 20
        aoc = 0 
        #aoc_vel = 0
        aoa = 0 / 180 * math.pi
        C_L = 1.1
        h = 0
        
        T = T0
        
        C_D = Cd0 + C_L**2 / (math.pi * AR * oswald)
        print(C_D)
        print(C_L)
        print(C_L/C_D)
        
        D = C_D * 0.5 * V * V * density * S
        L = C_L * 0.5 * V * V * density * S
        
        #aoc = math.asin((T-D)/W)
        
        #h = V * math.sin(aoc )
        
        N = W + D*math.sin(aoc) - L*math.cos(aoc) - T*math.sin(aoc+aoa)
        Df = friction*N
        acc = (T*math.cos(aoa) - D - Df*math.cos(aoc) - W*math.sin(aoc)) / mass
        #aoc_acc = (L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)) / (mass * V)
        
        V_history = []
        X_history = []
        t_history = []
        acc_history = []
        aoc_history = []
        h_history = []
        aoc_vel_history = []
        DF_history = []
        M_history = []
        M = V/sos
        length = -1
        L_history = []
        W_history = []
        T_history = []
        D_history = []
        density_history = []
        aoa_history = []
        C_L_history = []
        max_time = 3600
        equaldrag =False
        
        while True:
            if (t >= max_time):
                break
            
            V_history.append(V)
            X_history.append(X)
            t_history.append(t)
            acc_history.append(acc)
            aoc_history.append(aoc * 180 / math.pi)
            h_history.append(h)
            DF_history.append(Df)
            M_history.append(M)
            L_history.append(L)
            W_history.append(W)
            T_history.append(T)
            D_history.append(D)
            C_L_history.append(C_L)
            density_history.append(density)
            aoa_history.append(aoa * 180 / math.pi)

            
            V += acc * dt
            X += V * dt
            
            aoc_vel = (L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)) / (mass * V)
            if h <= 0:
                if aoc_vel < 0:
                    aoc_vel = 0
                #print('nom',(L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)))
                #print('den',(mass * V))
                #print('vel',aoc_vel)
            aoc_vel_history.append(aoc_vel*180/math.pi)
            aoc += aoc_vel * dt
            
            if h>0:
                if aoc_vel < 0:
                    if (aoa*180/math.pi < 10):
                        aoa +=  dt
                else:
                    if (aoa*180/math.pi > -10):
                        aoa -=  dt
           
            if h<10000:
                if aoc < 2:
                    if (aoa*180/math.pi < 10):
                        aoa += dt
                else:
                    if (aoa*180/math.pi > -10):
                        aoa -=  dt
            else:
                if aoc < 0:
                    if (aoa*180/math.pi < 10):
                        aoa +=  dt
                else:
                    if (aoa*180/math.pi > -10):
                        aoa -=  dt

            # if h > 1000:
            #     C_L = 0.1* aoa *180/math.pi + 0.3
            # else:
                C_L = 1.1
            
            C_D = Cd0 + C_L**2 / (math.pi * AR * oswald)
            
            h += V * math.sin(aoc) * dt
            
            _,_,density,sos = self.__ISA__(h) # sea level
            
            #T = T0 - (t/600)*T0/18
            
            #T = T0 * (density/1.225)

            if V < 300:
                if acc < 1:
                    if (T < 7000):
                        T += 1000* dt
                else:
                    if (T > 0):
                        T -= 1000* dt
            else:
                if acc < 0:
                    if (T < 7000):
                        T += 1000* dt
                else:
                    if (T > 0):
                        T -= 1000* dt

            #print(acc)
            #print(T)
            #print(C_L)
            '''
            if h < 12000 and equaldrag == False:
                T = T0 - 3000*t/max_time
            #
            elif h >= 12000:
                T = D*1.1
                equaldrag = True
                '''
        
            
            FF = TSFC * T * 0.000001
            mass -= (FF * dt)
            W = mass * g0
            
            M = V/sos
            
            
            
            D = C_D * 0.5 * V * V * density * S
            L = C_L * 0.5 * V * V * density * S
            N = W + D*math.sin(aoc) - L*math.cos(aoc) - T*math.sin(aoc+aoa)
            Df = friction*N
            if h > 0:
                Df = 0
                if length == -1:
                    length = X
            
            #aoc = math.asin((T-D)/W) * 180/math.pi
            
            #print('W',W)
            #print('L',L)
            #print('N',N)
            #print("V",V)
            
            acc = (T*math.cos(aoa) - D - Df*math.cos(aoc) - W*math.sin(aoc)) / mass
            #aoc_vel = (L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)) / (mass * V)
            
            t += dt

        print('time',t_history[-1])
        print("length",length)
        print(mass)
        print('T',T_history[-1])
        print('D',D_history[-1])
        print("L",L_history[-1])
        print("W",W_history[-1])
        print(acc)
        print(aoc * 180 / math.pi)
        print(aoa * 180 / math.pi)
        
        self.__plot_result__(t_history, C_L_history, "t [s]", "C_L [-]")
        self.__plot_result__(t_history, V_history, "t [s]", "V [m/s]")
        self.__plot_result__(t_history, M_history, "t [s]", "M [-]")
        self.__plot_result__(t_history, acc_history, "t [s]", "acc [m/s2]")
        self.__plot_result__(t_history, X_history, "t [s]", "X [m]")
        self.__plot_result__(t_history, aoc_history, "t [s]", "gamma [degrees]")
        self.__plot_result__(t_history, aoa_history, "t [s]", "aoa [degrees]")
        self.__plot_result__(t_history, h_history, "t [s]", "h [m]")
        self.__plot_result__(t_history, aoc_vel_history, "t [s]", "gammadot [degrees/s]")
        self.__plot_result__(t_history, density_history, "t [s]", "density [kg/m3]")
        #self.__plot_result__(t_history, DF_history, "t [s]", "friction [N]")
        self.__plot_result__(X_history, h_history, "x [m]", "h [m]")
        self.__plot_result__(t_history, L_history, "t [s]", "L [N]")
        self.__plot_result__(t_history, W_history, "t [s]", "W [N]")
        self.__plot_result__(t_history, T_history, "t [s]", "T [N]")
        self.__plot_result__(t_history, D_history, "t [s]", "D [N]")
        
        
        
            
            
            
        

if __name__ == "__main__":
    #FlightSim().level_flight(1500, 12000)
    FlightSim().ground_run(7000)
        