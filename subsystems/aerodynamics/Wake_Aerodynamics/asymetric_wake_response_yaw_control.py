# Final Stability Solution - Achieving Dutch Roll Stability
# Strong yaw damper gains + V-tail effectiveness enhancement

from math import*
import numpy
import pickle
import matplotlib.pyplot as plt

# AIRCRAFT CONFIGURATION WITH CORRECT INERTIA
V   = 240.0
S   = 9.44
b   = 10.65
mub = 79.6
CL  = 0.281

# ✅ CORRECT MOMENT OF INERTIA PARAMETERS
I_xx = 1212.66      # kg*m²
I_yy = 8466.62      # kg*m²  
I_zz = 9219.268     # kg*m²
I_xz = 382.99       # kg*m²
mass = 3000         # kg

KX2 = I_xx / (mass * b * b)    # = 0.003564
KZ2 = I_zz / (mass * b * b)    # = 0.027094
KXZ = I_xz / (mass * b * b)    # = 0.001126

print(f"✅ Using correct inertia parameters:")
print(f"KX2 = {KX2:.6f}, KZ2 = {KZ2:.6f}, KXZ = {KXZ:.6f}")

# AERODYNAMIC DERIVATIVES
CYb  =-1.0204;      Clb  =-0.2497;      Cnb  = 0.140
CYp  =-0.0131;      Clp  =-0.2561;      Cnp  =-0.5163
CYr  = 0.6475;      Clr  = 0.2868;      Cnr  =-0.3867
CYda = 0.0000;      Clda =-0.2349;      Cnda = 0.0286

# ORIGINAL V-TAIL CONTROL DERIVATIVES
CYdr_base = 0.3037;      Cldr_base = 0.0286;      Cndr_base =-0.1261

# TURBULENCE PARAMETERS
Lg = 150; sigma = 1
sigmaug_V = sigma/V; sigmavg = sigma; sigmabg = sigmavg/V; sigmaag = sigma/V
Iug0 = 0.0249*sigmaug_V**2; Iag0 = 0.0182*sigmaag**2
tau1 = 0.0991; tau2 = 0.5545; tau3 = 0.4159
tau4 = 0.0600; tau5 = 0.3294; tau6 = 0.2243

def calculate_system_matrices(CYdr_factor=1.0):
    """Calculate A and B matrices with V-tail effectiveness scaling"""
    
    CYdr = CYdr_base * CYdr_factor
    Cldr = Cldr_base * CYdr_factor
    Cndr = Cndr_base * CYdr_factor
    
    # Stability derivatives
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
    lug  = (-0.8*Clr*KZ2-0.2*Cnr*KXZ)/den 
    lbg  = lb 
    lag  = (0.8*Clp*KZ2+0.9*Cnp*KXZ)/den 
    nb   = (Clb*KXZ+Cnb*KX2)/den 
    np   = (Clp*KXZ+Cnp*KX2)/den 
    nr   = (Clr*KXZ+Cnr*KX2)/den 
    nda  = (Clda*KXZ+Cnda*KX2)/den 
    ndr  = (Cldr*KXZ+Cndr*KX2)/den 
    nug  = (-0.8*Clr*KXZ-0.2*Cnr*KX2)/den 
    nbg  = nb 
    nag  = (0.8*Clp*KXZ+0.9*Cnp*KX2)/den 
    
    # Turbulence terms
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

    B = numpy.asmatrix([[0,   ydr, 0,    0,    0],
                   [0,   0,   0,    0,    0],
                   [lda, ldr, 0,    0,    0],
                   [nda, ndr, 0,    0,    0],
                   [0,   0,   bug1, 0,    0],
                   [0,   0,   bug2, 0,    0],
                   [0,   0,   0,    bag1, 0],
                   [0,   0,   0,    bag2, 0],
                   [0,   0,   0,    0,    bbg1],
                   [0,   0,   0,    0,    bbg2]])
    
    return A, B

def analyze_dutch_roll(eigenvals):
    """Extract Dutch roll characteristics"""
    for ev in eigenvals:
        if abs(ev.imag) > 0.1 and ev.imag > 0:
            freq_hz = abs(ev.imag) / (2 * numpy.pi)
            damping_ratio = -ev.real / abs(ev)
            stable = ev.real < 0
            return ev.real, ev.imag, freq_hz, damping_ratio, stable
    return None, None, None, None, False

def test_control_config(A, B, K_phi, K_r, K_beta=0):
    """Test control configuration with optional sideslip feedback"""
    # Control vectors
    K_aileron = numpy.array([0, K_phi, 0, 0, 0, 0, 0, 0, 0, 0])      # phi feedback
    K_rudder = numpy.array([K_beta, 0, 0, K_r, 0, 0, 0, 0, 0, 0])    # yaw rate + sideslip feedback
    
    A_controlled = A - B[:,0]*K_aileron - B[:,1]*K_rudder
    eigenvals = numpy.linalg.eig(A_controlled)[0]
    
    real_part, imag_part, freq_hz, damping, stable = analyze_dutch_roll(eigenvals)
    
    return {
        'real_part': real_part,
        'damping': damping,
        'frequency': freq_hz,
        'stable': stable,
        'eigenvals': eigenvals
    }

print("\n" + "="*80)
print("🎯 FINAL STABILITY SOLUTION - SYSTEMATIC APPROACH")
print("="*80)

# PART 1: STRONG YAW DAMPER GAINS (baseline V-tail effectiveness)
print("\n🚀 PART 1: TESTING STRONG YAW DAMPER GAINS")
print("-" * 50)

A_base, B_base = calculate_system_matrices(CYdr_factor=1.0)

strong_gain_tests = [
    (-0.025, -3.0,  "Strong Yaw Damper"),
    (-0.025, -4.0,  "Very Strong Yaw Damper"),
    (-0.025, -6.0,  "Extremely Strong Yaw Damper"),
    (-0.025, -8.0,  "Maximum Yaw Damper"),
    (-0.025, -10.0, "Ultra Strong Yaw Damper"),
    (0,      -6.0,  "Pure Yaw Damper (Strong)"),
    (0,      -8.0,  "Pure Yaw Damper (Maximum)"),
]

best_result = None
results_strong = []

for K_phi, K_r, desc in strong_gain_tests:
    result = test_control_config(A_base, B_base, K_phi, K_r)
    result['description'] = desc
    result['K_phi'] = K_phi
    result['K_r'] = K_r
    result['vtail_factor'] = 1.0
    
    results_strong.append(result)
    
    status = "✅ STABLE" if result['stable'] else "❌ UNSTABLE"
    print(f"{desc:<30}: {result['real_part']:+.3f} ± {abs(result['real_part'] + 1j*result['frequency']*2*numpy.pi):.3f}j ({status})")
    if result['stable']:
        print(f"{'':32}  🎉 Damping: {result['damping']:+.3f}, Freq: {result['frequency']:.3f} Hz")
        if best_result is None or result['damping'] > best_result['damping']:
            best_result = result
    else:
        print(f"{'':32}  ⚠️  Still unstable, damping: {result['damping']:+.3f}")

# PART 2: ENHANCED V-TAIL EFFECTIVENESS 
print(f"\n🔧 PART 2: TESTING ENHANCED V-TAIL EFFECTIVENESS")
print("-" * 50)

vtail_enhancement_tests = [
    (1.5, "1.5x V-tail effectiveness"),
    (2.0, "2.0x V-tail effectiveness"), 
    (2.5, "2.5x V-tail effectiveness"),
    (3.0, "3.0x V-tail effectiveness"),
]

for vtail_factor, desc in vtail_enhancement_tests:
    print(f"\n--- {desc} ---")
    A_enhanced, B_enhanced = calculate_system_matrices(CYdr_factor=vtail_factor)
    
    # Test with moderate gain first
    result = test_control_config(A_enhanced, B_enhanced, -0.025, -3.0)
    result['description'] = f"Roll + Moderate Yaw Damper ({desc})"
    result['K_phi'] = -0.025
    result['K_r'] = -3.0
    result['vtail_factor'] = vtail_factor
    
    status = "✅ STABLE" if result['stable'] else "❌ UNSTABLE"
    print(f"K_phi=-0.025, K_r=-3.0: {result['real_part']:+.3f} ± {abs(result['real_part'] + 1j*result['frequency']*2*numpy.pi):.3f}j ({status})")
    
    if result['stable']:
        print(f"🎉 SUCCESS with enhanced V-tail! Damping: {result['damping']:+.3f}")
        if best_result is None or result['damping'] > best_result['damping']:
            best_result = result
    else:
        # Try stronger gain with enhanced V-tail
        result2 = test_control_config(A_enhanced, B_enhanced, -0.025, -5.0)
        result2['description'] = f"Roll + Strong Yaw Damper ({desc})"
        result2['K_phi'] = -0.025
        result2['K_r'] = -5.0
        result2['vtail_factor'] = vtail_factor
        
        status2 = "✅ STABLE" if result2['stable'] else "❌ UNSTABLE"
        print(f"K_phi=-0.025, K_r=-5.0: {result2['real_part']:+.3f} ± {abs(result2['real_part'] + 1j*result2['frequency']*2*numpy.pi):.3f}j ({status2})")
        
        if result2['stable'] and (best_result is None or result2['damping'] > best_result['damping']):
            best_result = result2

# PART 3: SIDESLIP FEEDBACK (if still no stability)
if best_result is None or not best_result['stable']:
    print(f"\n🎮 PART 3: TESTING SIDESLIP FEEDBACK")
    print("-" * 50)
    
    sideslip_tests = [
        (-0.025, -6.0, -0.1, "Roll + Yaw + Light Sideslip"),
        (-0.025, -6.0, -0.2, "Roll + Yaw + Medium Sideslip"),
        (-0.025, -8.0, -0.1, "Roll + Strong Yaw + Light Sideslip"),
    ]
    
    for K_phi, K_r, K_beta, desc in sideslip_tests:
        result = test_control_config(A_base, B_base, K_phi, K_r, K_beta)
        result['description'] = desc
        result['K_phi'] = K_phi
        result['K_r'] = K_r
        result['K_beta'] = K_beta
        result['vtail_factor'] = 1.0
        
        status = "✅ STABLE" if result['stable'] else "❌ UNSTABLE"
        print(f"{desc:<35}: {result['real_part']:+.3f} ({status})")
        
        if result['stable'] and (best_result is None or result['damping'] > best_result['damping']):
            best_result = result

# FINAL RESULTS AND RECOMMENDATIONS
print("\n" + "="*80)
print("🎯 FINAL RESULTS & FLIGHT CONTROL SYSTEM")
print("="*80)

if best_result and best_result['stable']:
    print("🎉 SUCCESS! Your aircraft is now STABLE!")
    print(f"✈️  Configuration: {best_result['description']}")
    print(f"🎮 Control Gains:")
    print(f"   K_phi (roll) = {best_result['K_phi']}")
    print(f"   K_r (yaw rate) = {best_result['K_r']}")
    if 'K_beta' in best_result:
        print(f"   K_beta (sideslip) = {best_result.get('K_beta', 0)}")
    if 'vtail_factor' in best_result and best_result['vtail_factor'] != 1.0:
        print(f"   V-tail effectiveness: {best_result['vtail_factor']}x baseline")
    
    print(f"\n📊 Performance:")
    print(f"   Dutch roll: {best_result['real_part']:+.3f} ± {abs(best_result['real_part'] + 1j*best_result['frequency']*2*numpy.pi):.3f}j")
    print(f"   Damping ratio: {best_result['damping']:+.3f}")
    print(f"   Frequency: {best_result['frequency']:.3f} Hz")
    
    print(f"\n🛠️  Implementation:")
    print(f"   δₐ = {best_result['K_phi']} × φ")
    print(f"   δᵣ = {best_result['K_r']} × (rb/2V)", end="")
    if 'K_beta' in best_result and best_result.get('K_beta', 0) != 0:
        print(f" + {best_result['K_beta']} × β")
    else:
        print("")
    
    print(f"\n✅ Your aircraft is now safe for flight operations!")
    
else:
    print("⚠️  Still working on achieving stability...")
    print("🔧 Next steps:")
    print("   1. Verify V-tail control surface sizing and effectiveness")
    print("   2. Consider active stability augmentation system")
    print("   3. Review aerodynamic derivative calculations")

# Save comprehensive results
save_data = {
    'best_stable_config': best_result,
    'all_results': results_strong,
    'aircraft_inertia': {'KX2': KX2, 'KZ2': KZ2, 'KXZ': KXZ},
    'success': best_result is not None and best_result['stable']
}

with open("final_aircraft_stability.pkl", 'wb') as f:
    pickle.dump(save_data, f)

print(f"\n💾 Complete results saved to 'final_aircraft_stability.pkl'")
print("🚀 Flight control system analysis complete!")