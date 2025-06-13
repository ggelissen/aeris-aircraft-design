"""
Simple Convergence Utilities for Master Design Process

This module provides minimal utilities to check convergence in the master loop.
Parameters are updated directly within analysis functions, not through utilities.
"""

from design_variables import DesignParameters
from typing import Dict


def get_key_parameters(params: DesignParameters) -> Dict[str, float]:
    """
    Extract key parameters for convergence monitoring.
    
    Parameters:
        params (DesignParameters): Design parameters object
        
    Returns:
        Dict[str, float]: Key parameters for convergence monitoring
    """
    
    return {
        'W_TO': params.weight.W_TO,
        'W_S': params.weight.W_S,
        'T_W': params.weight.T_W,
        'S_w': params.wing.S_w,
        'CD0': params.wing.C_D0 if params.wing.C_D0 is not None else 0.0
    }


def check_convergence(prev_params: Dict[str, float], curr_params: Dict[str, float], 
                     tolerance: float = 0.01) -> tuple[bool, Dict[str, float]]:
    """
    Check if the design has converged by comparing key parameters.
    
    Parameters:
        prev_params (Dict[str, float]): Parameters from previous iteration
        curr_params (Dict[str, float]): Parameters from current iteration  
        tolerance (float): Relative tolerance for convergence (default 1%)
        
    Returns:
        tuple[bool, Dict[str, float]]: (converged, relative_differences)
    """
    
    relative_diffs = {}
    converged = True
    
    for param_name in curr_params.keys():
        if param_name in prev_params:
            prev_val = prev_params[param_name]
            curr_val = curr_params[param_name]
            
            if prev_val != 0:
                rel_diff = abs((curr_val - prev_val) / prev_val)
                relative_diffs[param_name] = rel_diff
                
                if rel_diff > tolerance:
                    converged = False
            elif curr_val != 0:
                relative_diffs[param_name] = float('inf')
                converged = False
            else:
                relative_diffs[param_name] = 0.0
    
    return converged, relative_diffs


def print_convergence_status(iteration: int, relative_diffs: Dict[str, float], 
                           converged: bool, tolerance: float) -> None:
    """
    Print a formatted convergence status report.
    """
    
    print(f"\n{'='*50}")
    print(f"      CONVERGENCE CHECK - ITERATION {iteration}")
    print(f"{'='*50}")
    print(f"Tolerance: {tolerance:.1%}")
    print("-" * 50)
    
    for param_name, rel_diff in relative_diffs.items():
        status = "✅" if rel_diff <= tolerance else "❌"
        if rel_diff == float('inf'):
            print(f"{status} {param_name:<10}: {'∞':>8} {'(FAIL)':>8}")
        else:
            print(f"{status} {param_name:<10}: {rel_diff:>7.1%} {'(PASS)' if rel_diff <= tolerance else '(FAIL)':>8}")
    
    print("-" * 50)
    
    if converged:
        print("🎉 DESIGN CONVERGED!")
    else:
        print("🔄 Continuing iteration...")
    
    print("="*50)