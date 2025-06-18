# Enhanced cit2a.py with Yaw Damper Control
# Implementing yaw rate feedback to stabilize Dutch roll mode

from math import*
import numpy
import pickle
import matplotlib.pyplot as plt

# AIRCRAFT- AND FLIGHT CONDITION 'CRUISE FL400'.
V   = 240.0
S   = 9.44
b   = 10.65
mub = 79.6
KX2 = 0.012
KZ2 = 0.037
KXZ = 0.002
CL  = 0.281

I_xx = 1212.66     # Moment of inertia about x-axis (kg*m^2)
I_yy = 8466.62     # Moment of inertia about y-axis (kg*m^2)
I_zz = 9219.268     # Moment of inertia about z-axis (kg*m^2)
I_xz = 382.99     # Product of inertia xz-plane (kg*m^2)
CL  = 0.281

KX2 = I_xx/(3000 * 10.65**2)
KZ2 = I_zz/(3000 * 10.65**2)
KXZ = I_xz/(3000 * 10.65**2)

# TURBULENCE PARAMETERS
Lg        = 150
B         = b/(2*Lg)
sigma     = 1
sigmaug_V = sigma/V
sigmavg   = sigma
sigmabg   = sigmavg/V
sigmaag   = sigma/V

Iug0 = 0.0249*sigmaug_V**2
Iag0 = 0.0182*sigmaag**2

tau1 = 0.0991;      tau2 = 0.5545;      tau3 = 0.4159
tau4 = 0.0600;      tau5 = 0.3294;      tau6 = 0.2243

# AIRCRAFT ASYMMETRIC AERODYNAMIC DERIVATIVES 
CYb  =-1.0204;      Clb  =-0.2497;      Cnb  = 0.140
CYp  =-0.0131;      Clp  =-0.2561;      Cnp  =-0.5163
CYr  = 0.6475;      Clr  = 0.2868;      Cnr  =-0.3867
CYda = 0.0000;      Clda =-0.2349;      Cnda = 0.0286
CYdr = 0.3037;      Cldr = 0.0286;      Cndr =-0.1261
 
Clpw = 0.8*Clp;    Cnpw = 0.9*Cnp
Clrw = 0.7*Clr;    Cnrw = 0.2*Cnr

CYfb = 0
Clfb = 0
Cnfb = 0

# CALCULATION OF AIRCRAFT ASYMMETRIC STABILITY DERIVATIVES
yb   = (V/b)*CYb/(2*mub)
yphi = (V/b)*CL/(2*mub) 
yp   = (V/b)*CYp/(2*mub) 
yr   = (V/b)*(CYr-4*mub)/(2*mub) 
ybg  = yb 
ydr  = (V/b)*CYdr/(2*mub) 
den  = b*4*mub*(KX2*KZ2-KXZ**2)/V 
lb   = (Clb*KZ2+Cnb*KXZ)/den 
lp   = (Clp*KZ2+Cnp*KXZ)/den 
lr   = (Clr*KZ2+Cnr*KXZ)/den 
lda  = (Clda*KZ2+Cnda*KXZ)/den 
ldr  = (Cldr*KZ2+Cndr*KXZ)/den 
lug  = (-Clrw*KZ2-Cnrw*KXZ)/den 
lbg  = lb 
lag  = (Clpw*KZ2+Cnpw*KXZ)/den 
nb   = (Clb*KXZ+Cnb*KX2)/den 
np   = (Clp*KXZ+Cnp*KX2)/den 
nr   = (Clr*KXZ+Cnr*KX2)/den 
nda  = (Clda*KXZ+Cnda*KX2)/den 
ndr  = (Cldr*KXZ+Cndr*KX2)/den 
nug  = (-Clrw*KXZ-Cnrw*KX2)/den 
nbg  = nb 
nag  = (Clpw*KXZ+Cnpw*KX2)/den 
aug1 =-(V/Lg)**2*(1/(tau1*tau2)) 
aug2 =-(tau1+tau2)*(V/Lg)/(tau1*tau2) 
aag1 =-(V/Lg)**2*(1/(tau4*tau5)) 
aag2 =-(tau4+tau5)*(V/Lg)/(tau4*tau5) 
abg1 =-(V/Lg)**2 
abg2 =-2*(V/Lg) 
bug1 = tau3*sqrt(Iug0*V/Lg)/(tau1*tau2) 
bug2 = (1-tau3*(tau1+tau2)/(tau1*tau2))*sqrt(Iug0*(V/Lg)**3)/(tau1*tau2) 
bag1 = tau6*sqrt(Iag0*V/Lg)/(tau4*tau5) 
bag2 = (1-tau6*(tau4+tau5)/(tau4*tau5))*sqrt(Iag0*(V/Lg)**3)/(tau4*tau5) 
bbg1 = sigmabg*sqrt(3*V/Lg) 
bbg2 = (1-2*sqrt(3))*sigmabg*sqrt((V/Lg)**3) 

# STATE MATRIX A (10x10)
# States: [beta, phi, pb/2V, rb/2V, ug_, u_g*, alpha_g, alpha_g*, beta_g, betag*]
A = numpy.asmatrix([[yb, yphi, yp,    yr, 0,    0,    0,    0,    ybg,  0],
               [0,  0,    2*V/b, 0,  0,    0,    0,    0,    0,    0], 
               [lb, 0,    lp,    lr, lug,  0,    lag,  0,    lbg,  0],
               [nb, 0,    np,    nr, nug,  0,    nag,  0,    nbg,  0],
               [0,  0,    0,     0,  0,    1,    0,    0,    0,    0],
               [0,  0,    0,     0,  aug1, aug2, 0,    0,    0,    0],
               [0,  0,    0,     0,  0,    0,    0,    1,    0,    0],
               [0,  0,    0,     0,  0,    0,    aag1, aag2, 0,    0],
               [0,  0,    0,     0,  0,    0,    0,    0,    0,    1],
               [0,  0,    0,     0,  0,    0,    0,    0,    abg1, abg2]])

# INPUT MATRIX B (10x5)
# Inputs: [aileron, rudder, u_turb, alpha_turb, beta_turb]
B = numpy.asmatrix([[0,   ydr, 0,    0,    0],     # beta equation
               [0,   0,   0,    0,    0],     # phi equation
               [lda, ldr, 0,    0,    0],     # roll equation  
               [nda, ndr, 0,    0,    0],     # yaw equation
               [0,   0,   bug1, 0,    0],     # turbulence states
               [0,   0,   bug2, 0,    0],
               [0,   0,   0,    bag1, 0],
               [0,   0,   0,    bag2, 0],
               [0,   0,   0,    0,    bbg1],
               [0,   0,   0,    0,    bbg2]])

def analyze_eigenvalues(eigenvals, title):
    """Analyze and display eigenvalue characteristics"""
    print(f"\n=== {title} ===")
    print("Eigenvalues:", eigenvals)
    
    # Find complex pairs (Dutch roll)
    complex_modes = []
    real_modes = []
    
    for i, ev in enumerate(eigenvals):
        if abs(ev.imag) > 0.1:  # Complex eigenvalue
            if ev.imag > 0:  # Take only positive imaginary part
                complex_modes.append(ev)
        else:  # Real eigenvalue
            if abs(ev.real) < 10:  # Filter out turbulence modes
                real_modes.append(ev.real)
    
    # Analyze Dutch roll mode
    if complex_modes:
        ev = complex_modes[0]
        freq_hz = abs(ev.imag) / (2 * numpy.pi)
        damping_ratio = -ev.real / abs(ev)
        print(f"Dutch Roll: {ev.real:.3f} ± {abs(ev.imag):.3f}j")
        print(f"  Frequency: {freq_hz:.3f} Hz")
        print(f"  Damping: {damping_ratio:.3f}")
        print(f"  Stability: {'STABLE' if ev.real < 0 else 'UNSTABLE'}")
    
    # Analyze real modes
    real_modes.sort(key=abs)
    if len(real_modes) >= 2:
        print(f"Spiral Mode: {real_modes[0]:.6f} ({'STABLE' if real_modes[0] < 0 else 'UNSTABLE'})")
        print(f"Roll Mode: {real_modes[1]:.3f} ({'STABLE' if real_modes[1] < 0 else 'UNSTABLE'})")

# ANALYZE UNCONTROLLED SYSTEM
print("UNCONTROLLED AIRCRAFT ANALYSIS")
eigenvals_uncontrolled = numpy.linalg.eig(A)[0]
analyze_eigenvalues(eigenvals_uncontrolled, "UNCONTROLLED SYSTEM")

# CONTROL SYSTEM DESIGN
print("\n" + "="*60)
print("CONTROL SYSTEM DESIGN")
print("="*60)

# Control gains to test
test_cases = [
    # (K_phi, K_r, description)
    (-0.025, 0, "Original Roll Control Only"),
    (0, -0.5, "Yaw Damper Only (light)"),
    (0, -1.0, "Yaw Damper Only (medium)"),
    (0, -2.0, "Yaw Damper Only (strong)"),
    (-0.025, -0.5, "Combined: Roll + Light Yaw Damper"),
    (-0.025, -1.0, "Combined: Roll + Medium Yaw Damper"),
    (-0.025, -2.0, "Combined: Roll + Strong Yaw Damper"),
]

results = []

for K_phi, K_r, description in test_cases:
    print(f"\n--- {description} ---")
    print(f"K_phi = {K_phi}, K_r = {K_r}")
    
    # Control gain vector
    # States: [beta, phi, pb/2V, rb/2V, ug_, u_g*, alpha_g, alpha_g*, beta_g, betag*]
    K_aileron = numpy.array([0, K_phi, 0, 0, 0, 0, 0, 0, 0, 0])  # Aileron: phi feedback
    K_rudder = numpy.array([0, 0, 0, K_r, 0, 0, 0, 0, 0, 0])     # Rudder: yaw rate feedback
    
    # Controlled system: x_dot = (A - B_aileron*K_aileron - B_rudder*K_rudder) * x
    A_controlled = A - B[:,0]*K_aileron - B[:,1]*K_rudder
    
    # Analyze controlled system
    eigenvals_controlled = numpy.linalg.eig(A_controlled)[0]
    analyze_eigenvalues(eigenvals_controlled, f"CONTROLLED: {description}")
    
    # Store results for comparison
    results.append({
        'description': description,
        'K_phi': K_phi,
        'K_r': K_r,
        'eigenvals': eigenvals_controlled
    })

# FIND BEST CONFIGURATION
print("\n" + "="*60)
print("SUMMARY: FINDING BEST CONTROL CONFIGURATION")
print("="*60)

best_config = None
best_dutch_roll_damping = -999

for result in results:
    # Find Dutch roll mode
    for ev in result['eigenvals']:
        if abs(ev.imag) > 0.1 and ev.imag > 0:  # Dutch roll mode
            damping_ratio = -ev.real / abs(ev)
            stability = "STABLE" if ev.real < 0 else "UNSTABLE"
            
            print(f"{result['description']:<35}: Dutch Roll damping = {damping_ratio:+.3f} ({stability})")
            
            if ev.real < 0 and damping_ratio > best_dutch_roll_damping:
                best_dutch_roll_damping = damping_ratio
                best_config = result
            break

if best_config:
    print(f"\n🎯 RECOMMENDED CONFIGURATION: {best_config['description']}")
    print(f"   K_phi = {best_config['K_phi']}, K_r = {best_config['K_r']}")
    print(f"   Dutch Roll damping ratio = {best_dutch_roll_damping:.3f}")
else:
    print("\n⚠️  No stable configuration found - try stronger yaw damper gains!")

# SAVE RESULTS
print(f"\n💾 Saving results...")
save_vars = {
    "A": A, "B": B,
    "eigenvals_uncontrolled": eigenvals_uncontrolled,
    "results": results,
    "best_config": best_config,
    "V": V, "b": b, "S": S, "mub": mub
}

with open("yaw_damper_results.pkl", 'wb') as f:
    pickle.dump(save_vars, f)

print("Results saved to 'yaw_damper_results.pkl'")
print("\n✈️  Ready for implementation!")