import math
import matplotlib.pyplot as plt

class FlightSim:
    def __init__(self):
        """
        Initializes the FlightSim class.
        """
        pass

    def __ISA__(self, altitude: float):
        """
        Calculates atmospheric properties based on altitude using the International Standard Atmosphere (ISA) model.

        Parameters:
        altitude (float): Altitude in meters.

        Returns:
        tuple: Temperature (K), pressure (Pa), density (kg/m^3), and speed of sound (m/s) at the given altitude.
        """
        # ISA constants
        T0 = 288.15  # Sea level standard temperature (K)
        L = 0.0065   # Temperature lapse rate (K/m)
        p0 = 101325  # Sea level standard pressure (Pa)
        g0 = 9.80665 # Standard gravity (m/s^2)
        R = 287.05   # Specific gas constant for dry air (J/kg*K)
        gamma = 1.4  # Adiabatic index for dry air
        rho0 = 1.225 # Sea level standard density (kg/m^3)

        if altitude < 0:
            # Below sea level (assuming sea level conditions)
            T = 288.15
            p = p0
            rho = rho0
        elif altitude < 11000:
            # Troposphere (up to 11 km)
            T = T0 - L * altitude
            p = p0 * (1 - L/T0*altitude)**(g0/(R*L))
            rho = rho0 * (1 - L/T0*altitude)**(g0/(R*L)-1)
        else:
            # Stratosphere (above 11 km, constant temperature)
            T = T0 - L * 11000 # Temperature at 11 km
            p11 = p0 * (1 - L/T0*11000)**(g0/(R*L)) # Pressure at 11 km
            rho11 = rho0 * (1 - L/T0*11000)**(g0/(R*L)-1) # Density at 11 km
            p = p11 * math.exp(-g0/(R*T)*(altitude-11000))
            rho = rho11 * math.exp(-g0/(R*T)*(altitude-11000))

        a = (gamma * R * T)**0.5 # Speed of sound
        temperature = T
        pressure = p
        density = rho
        speed_of_sound = a

        return temperature,pressure,density,speed_of_sound

    def __plot_result__(self, x, y, x_label, y_label):
        """
        Plots a given set of data.

        Parameters:
        x (list): Data for the x-axis.
        y (list): Data for the y-axis.
        x_label (str): Label for the x-axis.
        y_label (str): Label for the y-axis.
        """
        plt.plot(x, y)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.show()

    def __sign__(self, x: float):
        """
        Returns the sign of a number.

        Parameters:
        x (float): The input number.

        Returns:
        int: -1 if x is negative, 1 otherwise.
        """
        if x < 0:
            return -1
        else:
            return 1

    def level_flight(self, T: float, altitude: float):
        """
        Simulates level flight conditions.

        Parameters:
        T (float): Thrust (N).
        altitude (float): Altitude (m).
        """
        # Get atmospheric properties at the given altitude
        _,_,density,speed_of_sound = self.__ISA__(altitude)
        print('sos', speed_of_sound)
        print('density',density)
        # Note: density is hardcoded here, might need to use the calculated one
        density = 0.311855
        TSFC = 20 # Thrust Specific Fuel Consumption

        # FF(g/s) = TFSC(g/Kns) * T(kN)
        Cd = 0.04 # Drag coefficient (Note: this is a constant value, likely simplified)
        S = 4     # Reference area (m^2)
        g0 = 9.80665 # Standard gravity (m/s^2)

        # Initial conditions
        mass = 3500 # Initial mass (kg)
        W = mass * g0 # Initial weight (N)
        V = 0       # Initial velocity (m/s)
        x = 0       # Initial horizontal distance (m)
        D = 1/2 * density * V * V * Cd * S # Initial drag (N)

        # Note: C_L is hardcoded, likely simplified
        C_L = 1.2 #W / (1/2 * density * V * V * S) # Lift coefficient
        L = W # Initial lift (N) - assuming level flight initially
        #T = 0 # Thrust (N) - this seems to be overwritten by the input parameter T
        EOM_X = T - D # Equation of motion in X (horizontal) direction
        EOM_Y = L - W # Equation of motion in Y (vertical) direction
        #L = W # Lift (N) - already set above
        acc_X = EOM_X/mass # Acceleration in X direction
        acc_Y = EOM_Y/mass # Acceleration in Y direction
        t = 0.0 # Initial time (s)
        dt = 0.1 # Time step (s)

        # History lists to store simulation data for plotting
        V_history = []
        acc_history = []
        x_history = []
        t_history = []
        M_history = []
        mass_history = []
        alt_history = []
        # range -> V/FF = max
        V_Y= 0 # Vertical velocity

        # Parameters for optimal lift and drag coefficients (likely for range/endurance)
        Cd0 = 0.0145 # Zero-lift drag coefficient (Roskam, bizjet)
        A = 9.0      # Aspect ratio
        e = 0.85     # Oswald efficiency factor
        C_L_opt = (1/3 * math.pi * A * e * Cd0)**0.5 # Optimal lift coefficient
        C_D_opt = 4/3 * Cd0 # Optimal drag coefficient

        print('CL/CD',C_L_opt/C_D_opt)

        # Thrust values related to optimal conditions (likely for analysis, not used in simulation loop)
        T_start = (C_D_opt/C_L_opt)*3150*9.80665
        T_avg = (C_D_opt/C_L_opt)*(3150*9.80665 - 0.5*10580)
        T_end = (C_D_opt/C_L_opt)*(3150*9.80665 - 10580)
        print("T",T_start)
        print("T",T_avg)
        print("T",T_end)


        # Simulation loop
        while True:
            if (t >= 2000): # Stop condition: simulation time reaches 2000 seconds
                break
            # Append current values to history lists
            V_history.append(V)
            acc_history.append(acc_X)
            mass_history.append(mass)
            x_history.append(x)
            t_history.append(t)
            M_history.append(V/speed_of_sound)
            alt_history.append(altitude)

            # Update state variables using Euler integration
            V += acc_X * dt
            x += V * dt

            # Recalculate forces and mass
            D = 1/2 * density * V * V * Cd * S # Drag (N)
            FF = TSFC * T / 1000 # Fuel flow (kg/s) - assuming TSFC is in g/kN/s and T is in N
            mass -= (FF * dt) # Update mass due to fuel burn
            W = mass * g0 # Update weight

            L = C_L * 1/2 * density * V * V  * S # Lift (N)

            # Update accelerations
            acc_Y = (L - W) / mass # Acceleration in Y direction
            V_Y += acc_Y *dt # Update vertical velocity
            altitude += V_Y * dt # Update altitude


            #print(V)
            #print(speed_of_sound)
            #print('D',D)
            #print('T',T)
            EOM_X = T - D # Equation of motion in X direction
            #print('EOM',EOM)
            acc_X = EOM_X/mass # Acceleration in X direction
            #print('acc',acc)
            t += dt # Increment time

        # Plot results
        self.__plot_result__(t_history, V_history, "t [s]", "V [m/s]")
        self.__plot_result__(t_history, M_history, "t [s]", "M [-]")
        self.__plot_result__(t_history, mass_history, "t [s]", "Mass [kg]")
        self.__plot_result__(t_history, alt_history, "t [s]", "Altitude [m]")
        #print(t_history)
        #print(V_history)

    def climb_flight(self, T, altitude):
        """
        Simulates climb flight conditions.

        Parameters:
        T (float): Thrust (N).
        altitude (float): Initial altitude (m).
        """
        # Get atmospheric properties
        _,_,density,speed_of_sound = self.__ISA__(altitude)
        print('sos', speed_of_sound)
        print('density',density)
        # Note: density is hardcoded here, might need to use the calculated one
        density = 0.311855

        Cd = 0.04 # Drag coefficient (Note: this is a constant value, likely simplified)
        S = 4     # Reference area (m^2)
        # initial:
        mass = 3500 # Initial mass (kg)
        V = 0       # Initial velocity (m/s)
        x = 0       # Initial horizontal distance (m)
        D = 1/2 * density * V * V * Cd * S # Initial drag (N)
        EOM = T - D # Equation of motion (simplified, likely only considering horizontal)
        acc = EOM/mass # Initial acceleration
        t = 0.0 # Initial time (s)
        dt = 0.1 # Time step (s)
        M = V / speed_of_sound # Initial Mach number

        # History lists to store simulation data for plotting
        V_history = []
        acc_history = []
        x_history = []
        t_history = []
        M_history = []

        # Simulation loop
        while True:
            if (t >= 1000): # Stop condition: simulation time reaches 1000 seconds
                break
            # Append current values to history lists
            V_history.append(V)
            acc_history.append(acc)
            x_history.append(x)
            t_history.append(t)
            M_history.append(V/speed_of_sound)

            # Update state variables using Euler integration
            V += acc * dt
            x += V * dt

            # Recalculate drag
            D = 1/2 * density * V * V * Cd * S # Drag (N)

            #print(V)
            #print(speed_of_sound)
            #print('D',D)
            #print('T',T)
            EOM = T - D # Equation of motion
            #print('EOM',EOM)
            acc = EOM/mass # Acceleration
            #print('acc',acc)
            t += dt # Increment time

        # Plot results
        self.__plot_result__(t_history, V_history, "t [s]", "V [m/s]")
        self.__plot_result__(t_history, M_history, "t [s]", "M [-]")
        #print(t_history)
        #print(V_history)


    def ground_run2(self, T0, mass0, S, Cd0, AR, oswald, TSFC, C_L,):
        """
        Simulates ground run (takeoff roll) with a focus on reaching takeoff speed.
        This function appears to use a recursive approach to find the required thrust for a target takeoff distance.

        Parameters:
        T0 (float): Initial Thrust (N).
        mass0 (float): Initial mass (kg).

        Returns:
        tuple: Initial Thrust (N), final horizontal distance (m), final velocity (m/s).
        """
        # Get atmospheric properties at sea level
        _,_,density,sos = self.__ISA__(0) # sea level
        mass = mass0 # Current mass (kg)
        g0 = 9.80665 # Standard gravity (m/s^2)
        W = mass * g0 # Current weight (N)
        V = 0 # Initial velocity (m/s)
        #S = 12 # Reference area (m^2)
        friction = 0.014 # Coefficient of rolling friction
        #Cd0 = 0.0172 # Zero-lift drag coefficient
        #AR = 9.0 # Aspect ratio
        #oswald = 0.85 # Oswald efficiency factor
        t = 0 # Initial time (s)
        dt = 0.001 # Time step (s)
        X = 0 # Initial horizontal distance (m)
        #TSFC = 14.646 # Thrust Specific Fuel Consumption
        aoc = 0 # Angle of climb (radians) - assumed 0 for ground run
        #aoc_vel = 0 # Angle of climb velocity (radians/s)
        aoa = 0 / 180 * math.pi # Angle of attack (radians) - assumed 0 for ground run
        #C_L = 1.1 # Lift coefficient (Note: this is a constant value, likely simplified for ground run)
        h = 0 # Initial altitude (m) - assumed 0 for ground run

        T = T0 # Current Thrust (N)

        # Calculate drag coefficient
        C_D = Cd0 + C_L**2 / (math.pi * AR * oswald)
        #print(C_D)
        #print(C_L)
        #print(C_L/C_D)

        # Calculate initial drag and lift
        D = C_D * 0.5 * V * V * density * S
        L = C_L * 0.5 * V * V * density * S

        #aoc = math.asin((T-D)/W) # This line is commented out, angle of climb is assumed 0

        #h = V * math.sin(aoc ) # This line is commented out, altitude is assumed 0

        # Calculate normal force and friction force
        N = W + D*math.sin(aoc) - L*math.cos(aoc) - T*math.sin(aoc+aoa)
        Df = friction*N # Friction force

        # Calculate initial acceleration using the equation of motion
        acc = (T*math.cos(aoa) - D - Df*math.cos(aoc) - W*math.sin(aoc)) / mass

        max_time = 360 # Maximum simulation time (s)

        # Simulation loop
        while True:
            # Check for takeoff condition (Lift >= Weight)
            if (L >= W):
                # Check if takeoff distance is close to the target (1800m)
                if 1800*0.9999< X < 1800*1.0001:
                    # If close, print results and return
                    print(T0)
                    print(X)
                    print(V/sos)
                    return T0,X,V
                # If takeoff distance is greater than target, reduce thrust and rerun
                if X > 1800:
                    return self.ground_run2(T0+(X-1800), mass0)
                # If takeoff distance is less than target, increase thrust and rerun
                else:
                    return self.ground_run2(T0-(1800-X), mass0)


            # Update state variables using Euler integration
            V += acc * dt
            X += V * dt

            # Recalculate forces and mass
            D = C_D * 0.5 * V * V * density * S # Drag (N)
            L = C_L * 0.5 * V * V * density * S # Lift (N)
            FF = TSFC * T * 0.000001 # Fuel flow (kg/s) - assuming TSFC is in g/kN/s and T is in N
            mass -= (FF * dt) # Update mass due to fuel burn
            W = mass * g0 # Update weight
            N = W + D*math.sin(aoc) - L*math.cos(aoc) - T*math.sin(aoc+aoa) # Normal force
            Df = friction*N # Friction force

            # Calculate acceleration
            acc = (T*math.cos(aoa) - D - Df*math.cos(aoc) - W*math.sin(aoc)) / mass

            t += dt # Increment time


    def ground_run(self, T0):
        """
        Simulates ground run (takeoff roll) and plots various parameters.

        Parameters:
        T0 (float): Initial Thrust (N).
        """
        # Get atmospheric properties at sea level
        _,_,density,sos = self.__ISA__(0) # sea level

        mass = 4200 # Initial mass (kg)
        g0 = 9.80665 # Standard gravity (m/s^2)
        W = mass * g0 # Initial weight (N)
        V = 0 # Initial velocity (m/s)
        S = 12 # Reference area (m^2)
        friction = 0.014 # Coefficient of rolling friction
        Cd0 = 0.0145 # Zero-lift drag coefficient
        AR = 9.0 # Aspect ratio
        oswald = 0.85 # Oswald efficiency factor
        t = 0 # Initial time (s)
        dt = 0.001 # Time step (s)
        X = 0 # Initial horizontal distance (m)
        TSFC = 20 # Thrust Specific Fuel Consumption
        aoc = 0 # Angle of climb (radians) - assumed 0 for ground run
        #aoc_vel = 0 # Angle of climb velocity (radians/s)
        aoa = 0 / 180 * math.pi # Angle of attack (radians) - assumed 0 for ground run
        # Note: C_L calculation seems to be a simplified linear model based on AoA
        C_L = 0.1* aoa *180/math.pi + 0.3 # Lift coefficient
        h = 0 # Initial altitude (m) - assumed 0 for ground run

        T = T0 # Current Thrust (N)

        # Calculate drag coefficient
        C_D = Cd0 + C_L**2 / (math.pi * AR * oswald)
        print(C_D)
        print(C_L)
        print(C_L/C_D)

        # Calculate initial drag and lift
        D = C_D * 0.5 * V * V * density * S
        L = C_L * 0.5 * V * V * density * S

        #aoc = math.asin((T-D)/W) # This line is commented out, angle of climb is assumed 0

        #h = V * math.sin(aoc ) # This line is commented out, altitude is assumed 0

        # Calculate normal force and friction force
        N = W + D*math.sin(aoc) - L*math.cos(aoc) - T*math.sin(aoc+aoa)
        Df = friction*N # Friction force

        # Calculate initial acceleration using the equation of motion
        acc = (T*math.cos(aoa) - D - Df*math.cos(aoc) - W*math.sin(aoc)) / mass
        #aoc_acc = (L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)) / (mass * V) # This line is commented out

        # History lists to store simulation data for plotting
        V_history = []
        X_history = []
        t_history = []
        acc_history = []
        aoc_history = []
        h_history = []
        aoc_vel_history = []
        DF_history = []
        M_history = []
        M = V/sos # Initial Mach number
        length = -1 # Variable to store takeoff distance
        L_history = []
        W_history = []
        T_history = []
        D_history = []
        density_history = []
        aoa_history = []
        C_L_history = []
        hvel_history = []
        max_time = 3600 # Maximum simulation time (s)
        equaldrag =False # Flag (purpose unclear from comments)
        hvel = 0 # Vertical velocity
        hacc = 0 # Vertical acceleration

        # Simulation loop
        while True:
            if (t >= max_time): # Stop condition: simulation time reaches max_time
                break

            # Append current values to history lists
            V_history.append(V)
            X_history.append(X)
            t_history.append(t)
            acc_history.append(acc)
            aoc_history.append(aoc * 180 / math.pi) # Store angle of climb in degrees
            h_history.append(h)
            DF_history.append(Df)
            M_history.append(M)
            L_history.append(L)
            W_history.append(W)
            T_history.append(T)
            D_history.append(D)
            C_L_history.append(C_L)
            hvel_history.append(hvel)
            density_history.append(density)
            aoa_history.append(aoa * 180 / math.pi) # Store angle of attack in degrees


            # Update state variables using Euler integration
            V += acc * dt
            X += V * dt

            # Calculate angle of climb velocity (gammadot)
            # This equation seems to be derived from the vertical equation of motion
            aoc_vel = (L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)) / (mass * V)
            # If on the ground (h <= 0) and aoc_vel is negative, set aoc_vel to 0 (cannot go below ground)
            if h <= 0:
                if aoc_vel < 0:
                    aoc_vel = 0
                #print('nom',(L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)))
                #print('den',(mass * V))
                #print('vel',aoc_vel)
            aoc_vel_history.append(aoc_vel*180/math.pi) # Store aoc_vel in degrees/s
            aoc += aoc_vel * dt # Update angle of climb

            # --- Angle of Attack Control Logic (commented out sections suggest experimentation) ---
            # The goal seems to be controlling AoA to reach a target altitude (12000m)
            # 'des' appears to be a control signal based on altitude error and vertical velocity/angle of climb rate
            des = (((12000 - h)/3000 - aoc*180/math.pi) - aoc_vel*180/math.pi)
            #des = ((1 - aoc*180/math.pi) - aoc_vel*180/math.pi) # Alternative 'des' calculation

            # Update angle of attack based on 'des' and AoA limits (-10 to 10 degrees)
            if aoa >= 10/180*math.pi:
                if des > 0:
                    aoa += 0 # If AoA is at upper limit and 'des' is positive, don't increase AoA
                else:
                    aoa += des * dt # Otherwise, update AoA based on 'des'
            elif aoa <= -10/180*math.pi:
                if des < 0:
                    aoa += 0 # If AoA is at lower limit and 'des' is negative, don't decrease AoA
                else:
                    aoa += des * dt # Otherwise, update AoA based on 'des'
            else:
                aoa += des * dt # If within limits, update AoA based on 'des'

            #print(des)
            #T += (((12000 - h) - aoc*180/math.pi) - aoc_vel*180/math.pi) # Commented out thrust control

            # --- Lift Coefficient Calculation ---
            # C_L is calculated based on the current angle of attack using a linear relationship
            # There are commented out sections suggesting different C_L models based on altitude
            # if h > 1000:
            #     C_L = 0.1* aoa *180/math.pi + 0.3
            # else:
            # if h <= 0:
            #     C_L = 0.1* aoa *180/math.pi + 1.0
            # else:
                C_L = 0.1* aoa *180/math.pi + 0.3 # Current C_L calculation


            # Recalculate drag coefficient based on updated C_L
            C_D = Cd0 + C_L**2 / (math.pi * AR * oswald)

            # Calculate vertical velocity and acceleration
            hvel = V * math.sin(aoc)
            # hacc = (hvel_history[-1] - hvel) / dt # This line is commented out, hacc is not used

            # Update altitude
            h += hvel * dt

            # Get updated atmospheric properties based on new altitude
            _,_,density,sos = self.__ISA__(h) # sea level

            # --- Thrust Control Logic (commented out sections suggest experimentation) ---
            # 'des' here seems to be a control signal based on Mach number error and acceleration
            des = ((0.85 - M)*3 - acc)
            #T = T0 * (density/1.225) # Commented out thrust calculation based on density

            # Update thrust based on 'des' and thrust limits (0 to 7000N)
            if T >= 7000:
                if des > 0:
                    T += 0 # If thrust is at upper limit and 'des' is positive, don't increase thrust
                else:
                    T += des * 100 * dt # Otherwise, update thrust based on 'des'
            elif T <= 0:
                if des < 0:
                    T += 0 # If thrust is at lower limit and 'des' is negative, don't decrease thrust
                else:
                    T += des * 100 * dt # Otherwise, update thrust based on 'des'
            else:
                T += des * 100 * dt # If within limits, update thrust based on 'des'

            # Commented out alternative thrust control logic based on Mach number and acceleration
            '''
            if M < 0.85:
                if (T < 7000):
                    T += 10* dt
                elif (T > 0):
                    T -= 10* dt
            else:
                if (0 < T < 7000):
                    T -= 10* dt
            '''

            '''
            if M < 0.85:
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
            '''
            #print(acc)
            #print(T)
            #print(C_L)

            # Commented out thrust control logic based on altitude and drag
            '''
            if h < 12000 and equaldrag == False:
                T = T0 - 3000*t/max_time
            #
            elif h >= 12000:
                T = D*1.1
                equaldrag = True
                '''


            # Calculate fuel flow and update mass
            FF = TSFC * T * 0.000001 # Fuel flow (kg/s) - assuming TSFC is in g/kN/s and T is in N
            mass -= (FF * dt) # Update mass due to fuel burn
            W = mass * g0 # Update weight

            # Update Mach number
            M = V/sos

            #print(T)


            # Recalculate drag and lift
            D = C_D * 0.5 * V * V * density * S # Drag (N)
            L = C_L * 0.5 * V * V * density * S # Lift (N)

            # Calculate normal force and friction force
            N = W + D*math.sin(aoc) - L*math.cos(aoc) - T*math.sin(aoc+aoa)
            Df = friction*N # Friction force

            # If airborne (h > 0), friction force is zero and record takeoff distance
            if h > 0:
                Df = 0
                if length == -1: # Record takeoff distance the first time the aircraft leaves the ground
                    length = X

            #aoc = math.asin((T-D)/W) * 180/math.pi # Commented out angle of climb calculation

            #print('W',W)
            #print('L',L)
            #print('N',N)
            #print("V",V)

            # Calculate acceleration using the equation of motion
            acc = (T*math.cos(aoa) - D - Df*math.cos(aoc) - W*math.sin(aoc)) / mass
            #aoc_vel = (L - math.cos(aoc)*W + T*math.sin(aoa) + Df*math.sin(aoc)) / (mass * V) # Commented out aoc_vel calculation

            t += dt # Increment time

        # Print final state variables
        print('time',t)
        print("length",length)
        print('mass',mass)
        print('T',T)
        print('D',D)
        print("L",L)
        print("W",W)
        print('acc',acc)
        print('aoc',aoc * 180 / math.pi)
        print('aoa',aoa * 180 / math.pi)
        print("CL",C_L)
        print("C_D",C_D)
        print("X",X)

        # Plot various parameters over time or distance
        self.__plot_result__(t_history, C_L_history, "t [s]", "C_L [-]")
        self.__plot_result__(t_history, hvel_history, "t [s]", "hdot [m/s]")
        self.__plot_result__(t_history, V_history, "t [s]", "V [m/s]")
        self.__plot_result__(t_history, M_history, "t [s]", "M [-]")
        self.__plot_result__(t_history, acc_history, "t [s]", "acc [m/s2]")
        self.__plot_result__(t_history, X_history, "t [s]", "X [m]")
        self.__plot_result__(t_history, aoc_history, "t [s]", "gamma [degrees]")
        self.__plot_result__(t_history, aoa_history, "t [s]", "aoa [degrees]")
        self.__plot_result__(t_history, h_history, "t [s]", "h [m]")
        self.__plot_result__(t_history, aoc_vel_history, "t [s]", "gammadot [degrees/s]")
        self.__plot_result__(t_history, density_history, "t [s]", "density [kg/m3]")
        self.__plot_result__(t_history, DF_history, "t [s]", "friction [N]")
        self.__plot_result__(X_history, h_history, "x [m]", "h [m]")
        self.__plot_result__(t_history, L_history, "t [s]", "L [N]")
        self.__plot_result__(t_history, W_history, "t [s]", "W [N]")
        self.__plot_result__(t_history, T_history, "t [s]", "T [N]")
        self.__plot_result__(t_history, D_history, "t [s]", "D [N]")


if __name__ == "__main__":
    #FlightSim().level_flight(1500, 12000)
    FlightSim().ground_run(6000)
    # FlightSim().ground_run2(7000,4000)
    # FlightSim().ground_run2(8000,5000)
    # FlightSim().ground_run2(1000,4000)
        