import os
import sys
import time
from typing import Dict, Tuple, List
import matplotlib
matplotlib.use('Agg')
# Add project paths
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import core modules
from design_variables import DesignParameters

def update_parameters_from_class_i(params: DesignParameters, class_i_results: Dict) -> None:
    """Update parameters with Class I results (inline)."""
    
    #print(f"    📝 Updating parameters from Class I results...")
    updates = 0
    
    # Weight parameters (and performance, but coming from initial weight estimations)
    if 'W_TO' in class_i_results:
        params.weight.W_TO = class_i_results['W_TO']
        #print(f"        ⚠️  W_TO updated to {params.weight.W_TO} (from Class I results)")
        updates += 1
    if 'W_E' in class_i_results:
        params.weight.W_E = class_i_results['W_E']
        updates += 1
    if 'W_OE' in class_i_results:
        params.weight.W_OE = class_i_results['W_OE']
        updates += 1
    if 'L_D_cruise' in class_i_results:
        params.performance.L_D_cruise = class_i_results['L_D_cruise']
        updates += 1
    if 'L_D_loiter' in class_i_results:
        params.performance.L_D_loiter = class_i_results['L_D_loiter']
        updates += 1
    if 'W_F_used' in class_i_results:
        params.weight.W_F_used = class_i_results['W_F_used']
        print(f"        ⚠️  W_F_used updated to {params.weight.W_F_used} (from Class I results)")
        updates += 1
    if 'W_F_res' in class_i_results:
        params.weight.W_F_res = class_i_results['W_F_res']
        print(f"        ⚠️  W_F_res updated to {params.weight.W_F_res} (from Class I results)")
        updates += 1
    if 'M_ff' in class_i_results:
        params.weight.M_ff = class_i_results['M_ff']
        #print(f"        ⚠️  M_ff updated to {params.weight.M_ff} (from Class I results)")
        updates += 1
    if 'W_F' in class_i_results:
        params.weight.W_F = class_i_results['W_F']
        print(f"        ⚠️  W_F updated to {params.weight.W_F} (from Class I results)")
        updates += 1
    if 'W_tfo' in class_i_results:
        params.weight.W_tfo = class_i_results['W_tfo']
        updates += 1

    # Thrust and wing loading parameters
    if 'T_W' in class_i_results:
        params.weight.T_W = class_i_results['T_W']
        updates += 1
    if 'W_S' in class_i_results:
        params.weight.W_S = class_i_results['W_S']
        params.weight.W_S_max = class_i_results['W_S']  # Assume max W/S is same as design W/S, as its given by the TW_SW graph
        updates += 1

    
    # Wing parameters  
    if 'Lambda_025c_w' in class_i_results:
        params.wing.Lambda_025c_w = class_i_results['Lambda_025c_w']
        updates += 1
    if 'b_w' in class_i_results:
        params.wing.b_w = class_i_results['b_w']
        updates += 1
    if 'S_w' in class_i_results:
        params.wing.S_w = class_i_results['S_w']
        params.wing.S_ref = class_i_results['S_w']  # Assume S_ref is same as S_w for now
    if 'lambda_w' in class_i_results:
        params.wing.lambda_w = class_i_results['lambda_w']
        updates += 1
    if 'Lambda_05c_w' in class_i_results:
        params.wing.Lambda_05_w = class_i_results['Lambda_05c_w']
        updates += 1
    if 'Lambda_LE_w' in class_i_results:
        params.wing.Lambda_0_w = class_i_results['Lambda_LE_w']
        updates += 1
    if 'root_chord' in class_i_results:
        params.wing.root_chord = class_i_results['root_chord']
        updates += 1
    if 'tip_chord' in class_i_results:
        params.wing.tip_chord = class_i_results['tip_chord']
        updates += 1
    if 'mac' in class_i_results:
        params.wing.mac = class_i_results['mac']
        updates += 1
    if 't_c_w_max' in class_i_results:
        params.wing.t_c_w_max = class_i_results['t_c_w_max']
        params.wing.t_c_w_r = class_i_results['t_c_w_max']  # Assume root = max
        updates += 1
    if 'y_LEMAC' in class_i_results:
        params.wing.y_LEMAC = class_i_results['y_LEMAC']
        updates += 1
    if 'Gamma_w' in class_i_results:
        params.wing.Gamma_w = class_i_results['Gamma_w']
        updates += 1
    
    #print(f"        ✅ Updated {updates} parameters from Class  out of {len(class_i_results)} Class I results")
    # Check which parameters were not updated
    # if updates < len(class_i_results): # commented as its not working properly
    #     not_updated = [key for key in class_i_results.keys() if key not in params.__dict__]
    #     if not_updated:
    #         print(f"        ⚠️  The following Class I results were not used to update parameters: {', '.join(not_updated)}")
    return params


def update_parameters_from_class_ii(params: DesignParameters, class_ii_results: Dict) -> None:
    """Update parameters with Class II results (inline)."""
    
    print(f"    📝 Updating parameters from Class II results...")
    updates = 0
    
    # Weight parameters (final converged values)
    if 'W_TO' in class_ii_results:
        params.weight.W_TO = class_ii_results['W_TO']
        updates += 1
    if 'W_E' in class_ii_results:
        params.weight.W_E = class_ii_results['W_E']
        updates += 1
    if 'W_OE' in class_ii_results:
        params.weight.W_OE = class_ii_results['W_OE']
        updates += 1
    if 'W_F' in class_ii_results:
        params.weight.W_F = class_ii_results['W_F']
        updates += 1
        print(f"        ⚠️  W_F updated to {params.weight.W_F} (from Class II results)")
    if 'W_F_used' in class_ii_results:
        params.weight.W_F_used = class_ii_results['W_F_used']
        updates += 1
        print(f"        ⚠️  W_F_used updated to {params.weight.W_F_used} (from Class II results)")
    # Empennage parameters
    # Update ALL relevant tail parameters directly (inline, simple approach)
    if 'S_h' in class_ii_results:
        params.empennage.S_h = class_ii_results['S_h']
        #print(f"        ⚠️  S_h updated to {params.empennage.S_h} (from Class II results)")
        updates += 1
    if 'S_v' in class_ii_results:
        params.empennage.S_v = class_ii_results['S_v']
        #print(f"        ⚠️  S_v updated to {params.empennage.S_v} (from Class II results)")
        updates += 1
    if 'S_t' in class_ii_results:
        params.empennage.S_t = class_ii_results['S_t']
        updates += 1
    if 'b_t' in class_ii_results:
        params.empennage.b_v = class_ii_results['b_t']
        updates += 1
    if 'dihedral_rad (gamma)' in class_ii_results:
        params.empennage.vtail_dihedral = class_ii_results['dihedral_rad (gamma)']
        updates += 1
    if 'c_root_t' in class_ii_results:
        params.empennage.c_r = class_ii_results['c_root_t']
        updates += 1
    if 'c_tip_t' in class_ii_results:
        params.empennage.c_t = class_ii_results['c_tip_t']
        updates += 1
    if 'taper_ratio_t' in class_ii_results:
        params.empennage.lambda_t = class_ii_results['taper_ratio_t']
        updates += 1
    if 'aspect_ratio_t' in class_ii_results:
        params.empennage.A_t = class_ii_results['aspect_ratio_t']
        updates += 1
    if 'Lambda_025c_t' in class_ii_results:
        params.empennage.Lambda_t_025c = class_ii_results['Lambda_025c_t']
        updates += 1
    if 't_c_t' in class_ii_results:
        if class_ii_results['t_c_t'] <= 0.0:
            print(f"        ⚠️  t_c_t is non-positive ({class_ii_results['t_c_t']:.4f}), not updating") # TODO! Currently negative
        params.empennage.t_c_t = class_ii_results['t_c_t']
        updates += 1
        
    
    # Drag parameters
    if 'CD0' in class_ii_results:
        params.wing.C_D0 = class_ii_results['CD0']
        updates += 1
    if 'CD0_tail' in class_ii_results:
        params.empennage.CD0_tail = class_ii_results['CD0_tail']
        updates += 1
    
    # Landing gear (simplified)
    if 'x_mlg' in class_ii_results:
        params.cg.x_cg_landing_gear = class_ii_results['x_mlg']
        updates += 1
    # TODO, add the rest of the landing gear parameters if needed
    #print(f"        ✅ Updated {updates} parameters from Class II")
    return params

def update_parameters_from_wing_optimization(params: DesignParameters, wing_results: Dict) -> None:
    """Update parameters with wing optimization results (inline)."""
    
    if not wing_results:
        print(f"    ⚠️  No wing optimization results to update")
        return
        
    #print(f"    📝 Updating parameters from wing optimization...")
    updates = 0
    
    # Core wing parameters
    if 'A_w_optimal' in wing_results:
        params.wing.A_w_target = wing_results['A_w_optimal']
        params.wing.A_w_actual = wing_results['A_w_optimal']
        updates += 1
    if 'S_w_optimal' in wing_results:
        params.wing.S_w = wing_results['S_w_optimal']
        params.wing.S_ref = wing_results['S_w_optimal']
        updates += 1
    if 'b_w_optimal' in wing_results:
        params.wing.b_w = wing_results['b_w_optimal']
        updates += 1
    if 'Lambda_025c_optimal' in wing_results:
        params.wing.Lambda_025c_w = wing_results['Lambda_025c_optimal']
        updates += 1
    if 'Lambda_LE_optimal' in wing_results:
        params.wing.Lambda_0_w = wing_results['Lambda_LE_optimal']
        updates += 1
    if 'Lambda_05c_optimal' in wing_results:
        params.wing.Lambda_05_w = wing_results['Lambda_05c_optimal']
        updates += 1
    if 'taper_ratio_optimal' in wing_results:
        params.wing.lambda_w = wing_results['taper_ratio_optimal']
        updates += 1
    if 'root_chord_optimal' in wing_results:
        params.wing.root_chord = wing_results['root_chord_optimal']
        updates += 1
    if 'tip_chord_optimal' in wing_results:
        params.wing.tip_chord = wing_results['tip_chord_optimal']
        updates += 1
    if 'MAC_optimal' in wing_results:
        params.wing.mac = wing_results['MAC_optimal']
        updates += 1
    if 'y_LEMAC_optimal' in wing_results:
        params.wing.y_LEMAC = wing_results['y_LEMAC_optimal']
        updates += 1
    if 't_c_optimal' in wing_results:
        params.wing.t_c_w_max = wing_results['t_c_optimal']
        params.wing.t_c_w_r = wing_results['t_c_optimal']
        updates += 1
    if 'dihedral_optimal' in wing_results:
        params.wing.Gamma_w = wing_results['dihedral_optimal']
        updates += 1
    if 'M_ff_optimal' in wing_results:
        params.weight.M_ff = wing_results['M_ff_optimal']
        updates += 1
    if 'M_ff_nominal' in wing_results:
        params.weight.M_ff_nominal = wing_results['M_ff_nominal']
        updates += 1
    if 'W_S_optimal' in wing_results:
        params.weight.W_S = wing_results['W_S_optimal']
        updates += 1
    if 'C_L_design_optimal' in wing_results:
        params.wing.CL = wing_results['C_L_design_optimal']
        updates += 1
    if 'L_D_optimal' in wing_results:
        params.performance.L_D_cruise = wing_results['L_D_optimal']
        updates += 1
    if 'L_D_loit_optimal' in wing_results:
        params.performance.L_D_loiter = wing_results['L_D_loit_optimal']
        updates += 1
    print(f"        ✅ Updated {updates} parameters from wing optimization")
    return params
