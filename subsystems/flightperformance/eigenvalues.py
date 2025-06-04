import sys
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.join(os.path.dirname(__file__), '..'), '..')))

from design_variables import DesignParameters

def short_period_eigenvalues(params: DesignParameters):

    muc = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.mac)
    KY2 = params.inertia.I_yy / (params.weight.M_TO * params.wing.mac**2)


    A = 2 * muc * KY2 * (2*muc - params.stability_aero.CZadot)
    B = -2*muc * KY2 * params.stability_aero.CZa - (2*muc + params.stability_aero.CZq) * params.stability_aero.Cmadot - (2*muc + params.stability_aero.Cmadot) * params.stability_aero.CZq
    C = params.stability_aero.CZa * params.stability_aero.Cmq - (2*muc + params.stability_aero.CZq) * params.stability_aero.Cma

    # Eigenvalues

    eigenvalues = np.roots([A, B, C])

    eigenvalues = eigenvalues
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/params.wing.mac


    # Half-period

    half_period = - np.log(0.5) / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed
    period = 2*np.pi/ np.imag(eigenvalues[0]) * params.wing.mac / params.cruise_speed
    time_constant = - 1 / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed

    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}
    
    return dict



def phugoid_eigenvalues(params: DesignParameters):

    muc = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.mac)
    # Quadratic equation:

    A = 2* muc * (params.stability_aero.CZa * params.stability_aero.Cmq - 2*muc * params.stability_aero.Cma)
    B = 2*muc * (params.stability_aero.CXu * params.stability_aero.Cma - params.stability_aero.Cmu * params.stability_aero.CXa) + params.stability_aero.Cmq * (params.stability_aero.CZu * params.stability_aero.CXa - params.stability_aero.CXu * params.stability_aero.CZa)
    C = params.stability_aero.CZ0 * (params.stability_aero.Cmu * params.stability_aero.CXa - params.stability_aero.CXu * params.stability_aero.Cma)

    # Eigenvalues

    eigenvalues = np.roots([A, B, C])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.mac

    # Half-period

    half_period = - np.log(0.5) / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed
    period = 2*np.pi/ np.imag(eigenvalues[0]) * params.wing.mac / params.cruise_speed
    time_constant = - 1 / np.real(eigenvalues[0]) * params.wing.mac / params.cruise_speed


    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}
    
    return dict


def aperiodic_roll_eigenvalues(params: DesignParameters):

    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)
    KX2 = params.inertia.I_xx / (params.weight.M_TO * params.wing.b_w**2)
    KZ2 = params.inertia.I_zz / (params.weight.M_TO * params.wing.b_w**2)
    JXZ = params.inertia.I_xz / (params.weight.M_TO * params.wing.b_w**2)

    eigenvalues = params.stability_aero.Clp / (4 * mub * KX2)
    half_period = - np.log(0.5) / np.real(eigenvalues) * params.wing.b_w / params.cruise_speed
    period = np.NaN
    time_constant = - 1 / np.real(eigenvalues) * params.wing.b_w / params.cruise_speed

    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant}
    
    return dict


def spiral_eigenvalues(params: DesignParameters):

    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)

    eigenvalues = 2*params.stability_aero.CL * (params.stability_aero.Clb*params.stability_aero.Cnr - params.stability_aero.Cnb*params.stability_aero.Clr) / (params.stability_aero.Clp * (params.stability_aero.CYb * params.stability_aero.Cnr + 4 * mub * params.stability_aero.Cnb) - params.stability_aero.Cnp * (params.stability_aero.CYb * params.stability_aero.Clr + 4 * mub * params.stability_aero.Clb))
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/c

    half_period = - np.log(0.5) / np.real(eigenvalues) * b / params.cruise_speed
    period = np.NaN
    time_constant = - 1 / np.real(eigenvalues) * b / params.cruise_speed

    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}
    
    return dict


def dutch_roll_eigenvalues(params: DesignParameters):

    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)
    KX2 = params.inertia.I_xx / (params.weight.M_TO * params.wing.b_w**2)
    KZ2 = params.inertia.I_zz / (params.weight.M_TO * params.wing.b_w**2)
    KXZ = params.inertia.I_xz / (params.weight.M_TO * params.wing.b_w**2)

    A = 4* mub**2 * (KZ2 * KX2 - KXZ**2)
    B = -mub * ((params.stability_aero.Clr + params.stability_aero.Cnp) * KXZ + params.stability_aero.Cnr * KX2 + params.stability_aero.Clp * KZ2)
    C = 2 * mub * (params.stability_aero.Cnb * KX2 + params.stability_aero.Clb * KXZ) + (params.stability_aero.Clp * params.stability_aero.Cnr - params.stability_aero.Clr * params.stability_aero.Cnp) / 4
    D = (params.stability_aero.Clb * params.stability_aero.Cnp - params.stability_aero.Cnb * params.stability_aero.Clp) / 2

    eigenvalues = np.roots([A, B, C, D])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/b

    half_period = - np.log(0.5) / np.real(eigenvalues) * params.wing.b_w / params.cruise_speed
    period = 2*np.pi/ np.imag(eigenvalues) * params.wing.b_w / params.cruise_speed
    time_constant = - 1 / np.real(eigenvalues) * params.wing.b_w / params.cruise_speed

    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}
    
    return dict


def asymmetric_eigenvalues(params: DesignParameters):

    mub = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.b_w)
    KX2 = params.inertia.I_xx / (params.weight.M_TO * params.wing.b_w**2)
    KZ2 = params.inertia.I_zz / (params.weight.M_TO * params.wing.b_w**2)
    KXZ = params.inertia.I_xz / (params.weight.M_TO * params.wing.b_w**2)

    # Define equations
    A = 16 * mub**3 * (KX2 * KZ2 - KXZ**2)
    B = -4 * mub**2 * (2 * params.stability_aero.CYb * (KX2 * KZ2 - KXZ**2) + params.stability_aero.Cnr * KX2 + params.stability_aero.Clp * KZ2 + (params.stability_aero.Clr + params.stability_aero.Cnp) * KXZ)
    C = 2 * mub * ((params.stability_aero.CYb * params.stability_aero.Cnr -params.stability_aero.CYr * params.stability_aero.Cnb) * KX2 + (params.stability_aero.CYb * params.stability_aero.Clp - params.stability_aero.Clb * params.stability_aero.CYp) * KZ2 + 
                ((params.stability_aero.CYb * params.stability_aero.Cnp - params.stability_aero.Cnb * params.stability_aero.CYp) + (params.stability_aero.CYb * params.stability_aero.Clr - params.stability_aero.Clb * params.stability_aero.CYr)) * KXZ +
                4 * mub * params.stability_aero.Cnb * KX2 + 4 * mub * params.stability_aero.Clb * KXZ + (1/2) * (params.stability_aero.Clp * params.stability_aero.Cnr - params.stability_aero.Cnp * params.stability_aero.Clr))
    D = (-4 * mub * params.performance.CL_cruise * (params.stability_aero.Clb * KZ2 + params.stability_aero.Cnb * KXZ) + 2 * mub * (params.stability_aero.Clb * params.stability_aero.Cnp - params.stability_aero.Cnb * params.stability_aero.Clp) +
                (1/2) * params.stability_aero.CYb * (params.stability_aero.Clr * params.stability_aero.Cnp - params.stability_aero.Cnr * params.stability_aero.Clp) + (1/2) * params.stability_aero.CYp * (params.stability_aero.Clb * params.stability_aero.Cnr - params.stability_aero.Cnb * params.stability_aero.Clr) +
                (1/2) * params.stability_aero.CYr * (params.stability_aero.Clp * params.stability_aero.Cnb - params.stability_aero.Cnp * params.stability_aero.Clb))
    E = params.performance.CL_cruise * (params.stability_aero.Clb * params.stability_aero.Cnr - params.stability_aero.Cnb * params.stability_aero.Clr)

    # Eigenvalues
    eigenvalues = np.roots([A, B, C, D, E])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/ params.wing.b_w

    # Half-period
    half_period =  np.log(0.5) / np.real(eigenvalues) * params.wing.b_w / params.cruise_speed
    period = np.NaN
    time_constant = - 1 / np.real(eigenvalues) * params.wing.b_w / params.cruise_speed

    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}
    
    return dict


def symmetric_eigenvalues(params: DesignParameters):

    muc = params.weight.M_TO / (params.cruise_density * params.wing.S_w * params.wing.mac)
    KY2 = params.inertia.I_yy / (params.weight.M_TO * params.wing.mac**2)
   
    A = 4 * muc**2 * KY2 * (params.stability_aero.CZadot - 2 * muc)
    B = (params.stability_aero.Cmadot * 2 * muc * (params.stability_aero.CZq + 2 * muc) - params.stability_aero.Cmq * 2 * muc * (params.stability_aero.CZadot - 2 * muc) -
        2 * muc * KY2 * (params.stability_aero.CXu * (params.stability_aero.CZadot - 2 * muc) - 2 * muc * params.stability_aero.CZa))
    C = (params.stability_aero.Cma * 2 * muc * (params.stability_aero.CZq + 2 * muc) - params.stability_aero.Cmadot * (2 * muc * params.stability_aero.CX0 + params.stability_aero.CXu * (params.stability_aero.CZq + 2 * muc)) +
       params.stability_aero.Cmq * (params.stability_aero.CXu * (params.stability_aero.CZadot - 2 * muc) - 2 * muc * params.stability_aero.CZa) + 2 * muc * KY2 * (params.stability_aero.CXa * params.stability_aero.CZu - params.stability_aero.CZa * params.stability_aero.CXu))
    D = (params.stability_aero.Cmu * (params.stability_aero.CXa * (params.stability_aero.CZq + 2 * muc) - params.stability_aero.CZ0 * (params.stability_aero.CZadot - 2 * muc)) -
       params.stability_aero.Cma * (2 * muc * params.stability_aero.CX0 + params.stability_aero.CXu * (params.stability_aero.CZq + 2 * muc)) +
       params.stability_aero.Cmadot * (params.stability_aero.CX0 * params.stability_aero.CXu - params.stability_aero.CZ0 * params.stability_aero.CZu) + params.stability_aero.Cmq * (params.stability_aero.CXu * params.stability_aero.CZa - params.stability_aero.CZu * params.stability_aero.CXa))
    E = -params.stability_aero.Cmu * (params.stability_aero.CX0 * params.stability_aero.CXa + params.stability_aero.CZ0 * params.stability_aero.CZa) + params.stability_aero.Cma * (params.stability_aero.CX0 * params.stability_aero.CXu + params.stability_aero.CZ0 * params.stability_aero.CZu)
    # Eigenvalues
    eigenvalues = np.roots([A, B, C, D, E])
    dimensioned_eigenvalues = eigenvalues * params.cruise_speed/c

    # Half-period
    half_period =  np.log(0.5) / np.real(eigenvalues) * params.wing.mac / params.cruise_speed
    period = np.NaN
    time_constant = - 1 / np.real(eigenvalues) * params.wing.mac / params.cruise_speed

    dict = {"eigenvalues": eigenvalues, "half_period": half_period, "period": period, "time_constant": time_constant, "dimensioned_eigenvalues": dimensioned_eigenvalues}
    
    return dict

def save_data(eigenvalue_data):
    
    df = pd.DataFrame(eigenvalue_data)
    filepath = os.path.join("modelling", "eigenvalue_data", f"eigenvalue_data.csv")
    df.to_csv(filepath, index=False)

    print("Data saved to eigenvalue_data.csv")


def run_eigenvalue_analysis(analytical_outputs, data):

    eigenvalue_data = {}

    eigenvalue_data["short_period"] = short_period_eigenvalues(analytical_outputs, data)
    eigenvalue_data["phugoid"] = phugoid_eigenvalues(analytical_outputs, data)
    eigenvalue_data["aperiodic_roll"] = aperiodic_roll_eigenvalues(analytical_outputs, data)
    eigenvalue_data["dutch_roll"] = dutch_roll_eigenvalues(analytical_outputs, data)
    eigenvalue_data["spiral"] = spiral_eigenvalues(analytical_outputs, data)

    eigenvalue_data["asymmetric"] = asymmetric_eigenvalues(analytical_outputs, data)
    eigenvalue_data["symmetric"] = symmetric_eigenvalues(analytical_outputs, data)


    save_data(eigenvalue_data)



if __name__ == "__main__":
    eigs = short_period_eigenvalues(DesignParameters())
    print(eigs)
    eigs = phugoid_eigenvalues(DesignParameters())
    print(eigs)
    eigs = aperiodic_roll_eigenvalues(DesignParameters())
    print(eigs)
    eigs = dutch_roll_eigenvalues(DesignParameters())
    print(eigs)
    eigs = spiral_eigenvalues(DesignParameters())
    print(eigs)