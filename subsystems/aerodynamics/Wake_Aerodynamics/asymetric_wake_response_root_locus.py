import numpy
import matplotlib.pyplot as plt
from math import sqrt

def cit2a_fun():
    """
    This function encapsulates the aircraft model parameters and calculations
    from cit2a_updated.py to return the state and input matrices.
    """
    # AIRCRAFT- AND FLIGHT CONDITION 'CRUISE FL400'.
    V = 240.0
    b = 10.65
    mub = 79.6
    CL = 0.281
    mass = 3000.0
    I_xx = 1212.66
    I_zz = 9219.268
    I_xz = 382.99
    
    # Non-dimensional inertia terms
    KX2 = I_xx / (mass * b * b)
    KZ2 = I_zz / (mass * b * b)
    KXZ = I_xz / (mass * b * b)

    # Turbulence Parameters
    Lg = 150.0  # Turbulence length scale [m]
    sigma = 2.0 # Turbulence intensity [m/s]
    sigmaug_V = sigma / V
    sigmabg = sigma / V
    sigmaag = sigma / V

    Iug0 = 0.0249 * sigmaug_V**2
    Iag0 = 0.0182 * sigmaag**2

    tau1 = 0.0991; tau2 = 0.5545; tau3 = 0.4159
    tau4 = 0.0600; tau5 = 0.3294; tau6 = 0.2243

    # Asymmetric Aerodynamic Derivatives
    CYb = -1.0204; Clb = -0.1597; Cnb = 0.140
    CYp = -0.0131; Clp = -0.2561; Cnp = -0.05163
    CYr = 0.6475; Clr = 0.2868; Cnr = -0.3867
    Clda = -0.2349; Cnda = 0.0286
    CYdr = 0.3037; Cldr = 0.0286; Cndr = -0.1261
    
    # Wing contribution corrections
    Clpw = 0.8 * Clp; Cnpw = 0.9 * Cnp
    Clrw = 0.7 * Clr; Cnrw = 0.2 * Cnr

    # Stability Derivatives Calculation
    yb = (V / b) * CYb / (2 * mub)
    yphi = (V / b) * CL / (2 * mub)
    yp = (V / b) * CYp / (2 * mub)
    yr = (V / b) * (CYr - 4 * mub) / (2 * mub)
    ybg = yb
    ydr = (V / b) * CYdr / (2 * mub)
    den = b * 4 * mub * (KX2 * KZ2 - KXZ**2) / V
    lb = (Clb * KZ2 + Cnb * KXZ) / den
    lp = (Clp * KZ2 + Cnp * KXZ) / den
    lr = (Clr * KZ2 + Cnr * KXZ) / den
    lda = (Clda * KZ2 + Cnda * KXZ) / den
    ldr = (Cldr * KZ2 + Cndr * KXZ) / den
    lug = (-Clrw * KZ2 - Cnrw * KXZ) / den
    lbg = lb
    lag = (Clpw * KZ2 + Cnpw * KXZ) / den
    nb = (Clb * KXZ + Cnb * KX2) / den
    np = (Clp * KXZ + Cnp * KX2) / den
    nr = (Clr * KXZ + Cnr * KX2) / den
    nda = (Clda * KXZ + Cnda * KX2) / den
    ndr = (Cldr * KXZ + Cndr * KX2) / den
    nug = (-Clrw * KXZ - Cnrw * KX2) / den
    nbg = nb
    nag = (Clpw * KXZ + Cnpw * KX2) / den

    # Turbulence filter states calculation
    aug1 = -(V / Lg)**2 * (1 / (tau1 * tau2))
    aug2 = -(tau1 + tau2) * (V / Lg) / (tau1 * tau2)
    aag1 = -(V / Lg)**2 * (1 / (tau4 * tau5))
    aag2 = -(tau4 + tau5) * (V / Lg) / (tau4 * tau5)
    abg1 = -(V / Lg)**2
    abg2 = -2 * (V / Lg)
    bug1 = tau3 * sqrt(Iug0 * V / Lg) / (tau1 * tau2)
    bug2 = (1 - tau3 * (tau1 + tau2) / (tau1 * tau2)) * sqrt(Iug0 * (V / Lg)**3) / (tau1 * tau2)
    bag1 = tau6 * sqrt(Iag0 * V / Lg) / (tau4 * tau5)
    bag2 = (1 - tau6 * (tau4 + tau5) / (tau4 * tau5)) * sqrt(Iag0 * (V / Lg)**3) / (tau4 * tau5)
    bbg1 = sigmabg * sqrt(3 * V / Lg)
    bbg2 = (1 - 2 * sqrt(3)) * sigmabg * sqrt((V / Lg)**3)
    
    # State Matrix A
    A = numpy.asmatrix([
        [yb, yphi, yp, yr, 0, 0, 0, 0, ybg, 0],
        [0, 0, 2 * V / b, 0, 0, 0, 0, 0, 0, 0],
        [lb, 0, lp, lr, lug, 0, lag, 0, lbg, 0],
        [nb, 0, np, nr, nug, 0, nag, 0, nbg, 0],
        [0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
        [0, 0, 0, 0, aug1, aug2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
        [0, 0, 0, 0, 0, 0, aag1, aag2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, abg1, abg2]
    ])

    # Input Matrix B
    B = numpy.asmatrix([
        [0, ydr, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [lda, ldr, 0, 0, 0],
        [nda, ndr, 0, 0, 0],
        [0, 0, bug1, 0, 0],
        [0, 0, bug2, 0, 0],
        [0, 0, 0, bag1, 0],
        [0, 0, 0, bag2, 0],
        [0, 0, 0, 0, bbg1],
        [0, 0, 0, 0, bbg2]
    ])
    
    return A, B

# --- Main script to generate the root locus plot ---

# Get the state and input matrices from the aircraft model
A, B = cit2a_fun()

# Define a range for the feedback gain Kphi. We'll vary it from 0 to -0.5
Kphi_range = numpy.linspace(0, -0.5, 500)

# Store the eigenvalues for each Kphi value
eigenvalues_list = []
for Kphi in Kphi_range:
    # Define the feedback matrix K for delta_a = K_phi * phi
    # Note that the state vector is [beta, phi, pb/2V, rb/2V, ...]
    K = numpy.array([0, Kphi, 0, 0, 0, 0, 0, 0, 0, 0])
    
    # Calculate the closed-loop state matrix: A_cl = A - B*K
    # We use the first column of B, which corresponds to aileron input (delta_a)
    A_controlled = A - B[:, 0] * K
    
    # Compute and store the eigenvalues
    eigvals = numpy.linalg.eigvals(A_controlled)
    eigenvalues_list.append(eigvals)

# Convert the list of eigenvalues to a NumPy array for easier plotting
eigenvalues = numpy.array(eigenvalues_list)

# --- Plotting the Root Locus ---

# Create the plot
plt.style.use('seaborn-v0_8-whitegrid')
fig, ax = plt.subplots(figsize=(12, 9))

# Plot the path of each eigenvalue (pole)
for i in range(eigenvalues.shape[1]):
    ax.plot(numpy.real(eigenvalues[:, i]), numpy.imag(eigenvalues[:, i]), 'b-', lw=1.5)

# Mark the open-loop poles (Kphi = 0) with 'x'
open_loop_poles = numpy.linalg.eigvals(A)
ax.plot(numpy.real(open_loop_poles), numpy.imag(open_loop_poles), 'kx', markersize=10, mew=2, label='Open-loop poles (Kphi=0)')

# Mark the poles for the two specific Kphi values from the script
# Kphi = -0.025
Kphi1 = -0.025
K1 = numpy.array([0, Kphi1, 0, 0, 0, 0, 0, 0, 0, 0])
A1 = A - B[:, 0] * K1
poles1 = numpy.linalg.eigvals(A1)
ax.plot(numpy.real(poles1), numpy.imag(poles1), 'go', markersize=8, label='Poles at Kphi = -0.025')

# Kphi = -0.1
Kphi2 = -0.1
K2 = numpy.array([0, Kphi2, 0, 0, 0, 0, 0, 0, 0, 0])
A2 = A - B[:, 0] * K2
poles2 = numpy.linalg.eigvals(A2)
ax.plot(numpy.real(poles2), numpy.imag(poles2), 'rs', markersize=8, label='Poles at Kphi = -0.1')

# --- Formatting the plot ---

# Add the stability boundary (imaginary axis)
ax.axvline(x=0, color='k', linestyle='--', lw=1.5)

# Set labels and title
ax.set_xlabel('Real Axis (Damping)', fontsize=14)
ax.set_ylabel('Imaginary Axis (Frequency)', fontsize=14)
#ax.set_title('Root Locus for Aileron Feedback Gain ($K_{\phi}$)', fontsize=16)

# Set plot limits to focus on the interesting region near the origin
ax.set_xlim(-8, 1)
ax.set_ylim(-5, 5)

# Add a legend
ax.legend(fontsize=12)

# Show the plot
plt.show()

# Save the figure
fig.savefig('root_locus_plot.pdf', bbox_inches='tight')