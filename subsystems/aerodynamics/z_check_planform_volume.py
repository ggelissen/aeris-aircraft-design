"""calculates fuel volume for the given planform. 
the planform can have multiple airfoil sections. 
this code would also be able to approximate the front and rear spar heights. 
the fuel volume is stored in between these spars.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Polygon
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.colors as mcolors
import os, sys

# Add path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from design_variables import WingParameters
from subsystems.aerodynamics.planform import calculate_initial_planform_params

def parse_airfoil_data(data_str: str) -> Dict[str, List[Tuple[float, float]]]:
    """
    Parse the airfoil coordinate data from string format into a dictionary.
    
    Args:
        data_str: String containing airfoil coordinate data
        
    Returns:
        Dictionary with 'upper' and 'lower' surface coordinates
    """
    coords = {'upper': [], 'lower': []}
    lines = data_str.strip().split('\n')
    
    # Skip header lines
    i = 0
    while i < len(lines) and (not lines[i].strip() or not lines[i][0].isdigit()):
        i += 1
        
    # Parse coordinates
    upper = []
    lower = []
    for line in lines[i:]:
        if not line.strip():
            continue
        try:
            x, y = map(float, line.strip().split()[:2])
            if len(upper) == 0 or x >= upper[-1][0]:
                upper.append((x, y))
            else:
                lower.insert(0, (x, y))
        except (ValueError, IndexError):
            continue
            
    coords['upper'] = upper
    coords['lower'] = lower
    return coords

def interpolate_coords(coords: List[Tuple[float, float]], x: float) -> float:
    """
    Interpolate y coordinate at a given x coordinate between airfoil points.
    
    Args:
        coords: List of (x,y) coordinate tuples defining the airfoil section
        x: X-coordinate at which to find the y value
    
    Returns:
        Interpolated y-coordinate
    """
    for i in range(len(coords) - 1):
        x1, y1 = coords[i]
        x2, y2 = coords[i + 1]
        
        if x1 <= x <= x2:
            # Linear interpolation
            if x2 - x1 == 0:
                return y1
            return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
            
    return 0.0  # Return 0 if x is outside range

def get_section_height(coords: Dict[str, List[Tuple[float, float]]], x: float) -> float:
    """
    Calculate the airfoil height at a given x position.
    
    Args:
        coords: Dictionary containing upper and lower surface coordinates
        x: X-coordinate at which to find the height
    
    Returns:
        Height of the airfoil at position x in normalized coordinates
    """
    y_upper = interpolate_coords(coords['upper'], x)
    y_lower = interpolate_coords(coords['lower'], x)
    return y_upper - y_lower

def calculate_section_area(coords: Dict[str, List[Tuple[float, float]]], 
                         chord: float, 
                         front_spar_x: float, 
                         rear_spar_x: float,
                         sweep_rad: Optional[float] = 0.0,
                         dihedral_rad: Optional[float] = 0.0,
                         twist_rad: Optional[float] = 0.0,
                         y_position: Optional[float] = 0.0,
                         semi_span: Optional[float] = 1.0,
                         num_points: int = 50) -> Tuple[float, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate section area accounting for airfoil curvature and wing geometry using numerical integration.
    
    Args:
        coords: Dictionary containing upper and lower surface coordinates
        chord: Chord length at this section in meters
        front_spar_x: Front spar position (fraction of chord)
        rear_spar_x: Rear spar position (fraction of chord)
        sweep_rad: Wing sweep angle in radians (optional)
        dihedral_rad: Wing dihedral angle in radians (optional)
        twist_rad: Wing twist angle in radians (optional)
        y_position: Spanwise position for sweep calculation (optional)
        semi_span: Half span length for geometric calculations (optional)
        num_points: Number of points to use for integration
        
    Returns:
        Tuple of (area, x_points, heights, z_points) where:
        - area is in m²
        - x_points are chordwise positions accounting for sweep
        - heights are section thicknesses
        - z_points are vertical positions accounting for dihedral
    """
    # Calculate points along chord for integration
    x_points = np.linspace(front_spar_x, rear_spar_x, num_points)
    heights = np.array([get_section_height(coords, x) for x in x_points])
    
    # Scale coordinates to actual dimensions
    x_points_scaled = x_points * chord
    heights_scaled = heights * chord
    
    # Initialize z-coordinates accounting for dihedral
    z_points = np.zeros_like(x_points_scaled)
    
    # Account for sweep angle by shifting x-coordinates
    if sweep_rad != 0.0:
        sweep_offset = y_position * np.tan(sweep_rad)
        x_points_scaled += sweep_offset
    
    # Apply dihedral to vertical positions
    if dihedral_rad != 0.0:
        # Calculate vertical displacement due to dihedral
        dihedral_offset = y_position * np.sin(dihedral_rad)
        z_points += dihedral_offset
        # Adjust heights for dihedral angle
        heights_scaled *= np.cos(dihedral_rad)
    
    # Apply twist angle if present 
    # Note: Twist increases linearly from root to tip
    if twist_rad != 0.0:
        # Calculate local twist based on spanwise position
        local_twist = twist_rad * (y_position / semi_span)
        cos_twist = np.cos(local_twist)
        sin_twist = np.sin(local_twist)
        
        # Apply rotation matrix to coordinates
        x_rotated = x_points_scaled * cos_twist - heights_scaled * sin_twist
        h_rotated = x_points_scaled * sin_twist + heights_scaled * cos_twist
        
        x_points_scaled = x_rotated
        heights_scaled = h_rotated
    
    # Calculate section area using trapezoidal integration
    area = np.trapz(heights_scaled, x_points_scaled)
    
    return area, x_points_scaled, heights_scaled, z_points

def calculate_fuel_volume(airfoil_data: str, root_chord: float, tip_chord: float, 
                          semi_span: float, front_spar_x: float = 0.15, 
                          rear_spar_x: float = 0.65,
                          wing_params: Optional[WingParameters] = None,
                          num_sections: int = 20,
                          num_curve_points: int = 50) -> Tuple[float, Dict]:
    """
    Calculate the fuel volume in the wing between spars, accounting for wing geometry.
    
    Args:
        airfoil_data: String containing airfoil coordinate data
        root_chord: Root chord length in meters
        tip_chord: Tip chord length in meters
        semi_span: Half span length in meters
        front_spar_x: Front spar position (fraction of chord)
        rear_spar_x: Rear spar position (fraction of chord)
        wing_params: Optional WingParameters instance for geometric parameters
        num_sections: Number of spanwise sections for integration
        num_curve_points: Number of points to use for curvature calculation
        
    Returns:
        Tuple of (total fuel volume in m³, dictionary with section details)
    """
    # Get geometric parameters
    geo_params = get_wing_geometric_params(wing_params)
    sweep_rad = geo_params['sweep_rad']
    dihedral_rad = geo_params['dihedral_rad']
    twist_rad = geo_params['twist_rad']
    
    # Parse airfoil coordinates
    coords = parse_airfoil_data(airfoil_data)
    
    # Generate spanwise sections
    y_positions = np.linspace(0, semi_span, num_sections)
    chord_lengths = np.interp(y_positions, 
                             [0, semi_span], 
                             [root_chord, tip_chord])
    
    # Calculate volume using trapezoidal integration
    volume = 0
    section_details = []
    
    for i in range(num_sections - 1):
        # Average chord at this section
        avg_chord = (chord_lengths[i] + chord_lengths[i+1]) / 2
        avg_y_pos = (y_positions[i] + y_positions[i+1]) / 2
        
        # Calculate section properties with all geometric effects
        area, x_points, heights, z_points = calculate_section_area(
            coords, avg_chord, front_spar_x, rear_spar_x,
            sweep_rad, dihedral_rad, twist_rad,
            avg_y_pos, semi_span, num_curve_points
        )
        
        # Calculate true spanwise segment length accounting for dihedral
        dy = y_positions[i+1] - y_positions[i]
        if dihedral_rad != 0.0:
            dy = dy / np.cos(dihedral_rad)  # True length along dihedral angle
        
        # Volume of this spanwise segment
        section_volume = area * dy
        volume += section_volume
        
        # Store section details with geometric data
        section_details.append({
            'y_position': avg_y_pos,
            'chord': avg_chord,
            'area': area,
            'volume': section_volume,
            'curve_x': x_points,
            'curve_heights': heights,
            'curve_z': z_points,
            'true_dy': dy
        })
    
    # Total volume for both wings
    total_volume = 2 * volume
    
    return total_volume, {
        'sections': section_details,
        'parameters': {
            'front_spar_x': front_spar_x,
            'rear_spar_x': rear_spar_x,
            'sweep_rad': sweep_rad,
            'dihedral_rad': dihedral_rad,
            'twist_rad': twist_rad,
            'num_sections': num_sections,
            'num_curve_points': num_curve_points
        }
    }

def plot_wing_fuel_volume(airfoil_data: str, root_chord: float, tip_chord: float, 
                         semi_span: float, front_spar_x: float = 0.15, 
                         rear_spar_x: float = 0.65,
                         wing_params: Optional[WingParameters] = None,
                         num_sections: int = 20,
                         show_sections: bool = True, 
                         show_spars: bool = True,
                         show_parameters: bool = True,
                         colormap: str = 'YlOrRd') -> None:
    """
    Create a 3D visualization of the wing fuel volume with geometric effects.
    
    Args:
        airfoil_data: String containing airfoil coordinate data
        root_chord: Root chord length in meters
        tip_chord: Tip chord length in meters
        semi_span: Half span length in meters
        front_spar_x: Front spar position (fraction of chord)
        rear_spar_x: Rear spar position (fraction of chord)
        wing_params: Optional WingParameters instance for geometric parameters
        num_sections: Number of spanwise sections for visualization
        show_sections: Whether to show section boundaries
        show_spars: Whether to show spar positions
        show_parameters: Whether to show geometric parameters in title
        colormap: Name of matplotlib colormap to use for volume visualization
    """
    # Calculate volumes with geometric parameters
    volume, details = calculate_fuel_volume(
        airfoil_data, root_chord, tip_chord, semi_span,
        front_spar_x, rear_spar_x, wing_params,
        num_sections
    )
    geo_params = details['parameters']
    
    # Create figure
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Parse section data
    sections = details['sections']
    y_positions = [section['y_position'] for section in sections]
    volumes = [section['volume'] for section in sections]
    
    # Create color mapping
    norm_volumes = (volumes - min(volumes)) / (max(volumes) - min(volumes))
    cmap = plt.get_cmap(colormap)
    
    # Plot both wings (mirrored)
    for mirror in [-1, 1]:
        for i in range(len(sections)-1):
            section = sections[i]
            next_section = sections[i+1]
              # Get curved surface points with geometric effects already applied
            x_curve_curr = section['curve_x']
            z_curve_curr = section['curve_heights']
            z_offset_curr = section['curve_z']
            
            x_curve_next = next_section['curve_x']
            z_curve_next = next_section['curve_heights']
            z_offset_next = next_section['curve_z']
            
            # Mirror y-positions and adjust heights for symmetry
            y_pos = mirror * section['y_position']
            next_y_pos = mirror * next_section['y_position']
            
            # Scale heights to maintain symmetry across span
            z_scale = 1.0  # Keep original height scaling on positive side
            if mirror < 0:
                # Ensure height scaling matches positive side
                z_curve_curr = z_curve_curr * z_scale
                z_curve_next = z_curve_next * z_scale
                z_offset_curr = z_offset_curr * z_scale
                z_offset_next = z_offset_next * z_scale
            
            # Create surface patches for upper and lower surfaces
            for surface in ['upper', 'lower']:
                # Create points arrays for the surface
                x_points = []
                y_points = []
                z_points = []
                
                # Get z values based on surface
                z_vals_curr = z_curve_curr if surface == 'upper' else -z_curve_curr
                z_vals_next = z_curve_next if surface == 'upper' else -z_curve_next
                
                # Add dihedral offset
                z_vals_curr += z_offset_curr
                z_vals_next += z_offset_next
                
                # Add points for the curved surface
                for j in range(len(x_curve_curr)):
                    x_points.extend([x_curve_curr[j], x_curve_next[j]])
                    y_points.extend([y_pos, next_y_pos])
                    z_points.extend([z_vals_curr[j], z_vals_next[j]])
                
                # Create triangulation for the curved surface
                triangles = []
                n_curve_points = len(x_curve_curr)
                for j in range(n_curve_points - 1):
                    idx1 = 2 * j
                    idx2 = 2 * j + 1
                    idx3 = 2 * j + 2
                    idx4 = 2 * j + 3
                    triangles.extend([[idx1, idx2, idx3], [idx2, idx4, idx3]])
                
                # Create faces and add to plot
                faces = []
                points = np.array(list(zip(x_points, y_points, z_points)))
                for triangle in triangles:
                    faces.append([points[idx] for idx in triangle])
                
                color = cmap(norm_volumes[i])
                poly = Poly3DCollection(faces, alpha=0.6)
                poly.set_facecolor(color)
                poly.set_edgecolor('gray' if show_sections else 'none')
                ax.add_collection3d(poly)
            
            # Add spar visualization if enabled
            if show_spars:
                for spar_x in [section['chord'] * front_spar_x, section['chord'] * rear_spar_x]:
                    # Find heights at spar position
                    idx = np.argmin(np.abs(x_curve_curr - spar_x))
                    spar_height_curr = z_curve_curr[idx]
                    spar_z_curr = z_offset_curr[idx]
                    
                    idx = np.argmin(np.abs(x_curve_next - spar_x))
                    spar_height_next = z_curve_next[idx]
                    spar_z_next = z_offset_next[idx]
                      # Create spar face with geometric transformations
                    # Find x-coordinates accounting for sweep
                    sweep_offset_curr = section['y_position'] * np.tan(geo_params['sweep_rad'])
                    sweep_offset_next = next_section['y_position'] * np.tan(geo_params['sweep_rad'])
                    
                    # Apply transformations to spar positions
                    spar_x_curr = spar_x + sweep_offset_curr
                    spar_x_next = spar_x + sweep_offset_next
                    
                    # Create spar face with all geometric effects
                    spar_vertices = [
                        [spar_x_curr, y_pos, spar_height_curr + spar_z_curr],
                        [spar_x_next, next_y_pos, spar_height_next + spar_z_next],
                        [spar_x_next, next_y_pos, -spar_height_next + spar_z_next],
                        [spar_x_curr, y_pos, -spar_height_curr + spar_z_curr]
                    ]
                    
                    spar_poly = Poly3DCollection([spar_vertices], alpha=0.3)
                    spar_poly.set_facecolor('gray')
                    spar_poly.set_edgecolor('black')
                    ax.add_collection3d(spar_poly)
    
    # Set labels and title with geometry info
    ax.set_xlabel('Chord Position (m)')
    ax.set_ylabel('Span Position (m)')
    ax.set_zlabel('Height (m)')
    
    title = f'Wing Fuel Volume Distribution\nTotal Volume: {volume:.2f} m³'
    if show_parameters:
        sweep_deg = np.degrees(geo_params['sweep_rad'])
        dihedral_deg = np.degrees(geo_params['dihedral_rad'])
        twist_deg = np.degrees(geo_params['twist_rad'])
        title += f'\nΛ(c/4)={sweep_deg:.1f}°, Γ={dihedral_deg:.1f}°, ε={twist_deg:.1f}°'
    ax.set_title(title)
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap)
    sm.set_array(volumes)
    plt.colorbar(sm, ax=ax, label='Section Volume (m³)')
    
    # Set axis limits
    max_chord = max(root_chord, tip_chord)
    max_sweep_offset = semi_span * np.tan(geo_params['sweep_rad'])
    max_height = max([max(abs(section['curve_heights'])) for section in sections])
    max_dihedral_offset = semi_span * np.sin(geo_params['dihedral_rad'])
    
    ax.set_xlim(0, max_chord + max_sweep_offset)
    ax.set_ylim(-semi_span, semi_span)
    ax.set_zlim(-max_height * 1.2 - max_dihedral_offset, 
                max_height * 1.2 + max_dihedral_offset)
    
    # Set equal aspect ratio
    ax.set_box_aspect([2, 3, 1])
    
    plt.show()

def get_wing_geometric_params(wing_params: Optional[WingParameters] = None) -> Dict:
    """
    Get wing geometric parameters either from provided WingParameters 
    or calculate default values.
    
    Args:
        wing_params: Optional WingParameters instance
        
    Returns:
        Dictionary containing sweep, dihedral, and twist angles in radians
    """
    if wing_params is not None:
        return {
            'sweep_rad': wing_params.Lambda_w_quarter,    # Quarter-chord sweep
            'dihedral_rad': wing_params.Gamma_w,         # Dihedral angle
            'twist_rad': wing_params.epsilon_t_quarter_chord  # Twist angle
        }
    else:
        # Default values if no parameters provided
        return {
            'sweep_rad': 32*np.pi/180,  # ~32 degrees
            'dihedral_rad': 0.0175,     # ~1 degree
            'twist_rad': 0.0           # 0 degrees
        }

if __name__ == "__main__":
    # Example usage with the SC(2)-0714 airfoil data
    airfoil_data = """SC(2)-0714 Supercritical airfoil
0 0
0.002 0.0095
0.005 0.0158
0.01 0.0219
0.02 0.0293
0.03 0.0343
0.04 0.0381
0.05 0.0411
0.07 0.0462
0.1 0.0518
0.12 0.0548
0.15 0.0585
0.17 0.0606
0.2 0.0632
0.22 0.0646
0.25 0.0664
0.27 0.0673
0.3 0.0685
0.33 0.0692
0.35 0.0696
0.38 0.0698
0.4 0.0697
0.43 0.0695
0.45 0.0692
0.48 0.0684
0.5 0.0678
0.53 0.0666
0.55 0.0656
0.57 0.0645
0.6 0.0625
0.62 0.061
0.65 0.0585
0.68 0.0555
0.7 0.0533
0.72 0.0509
0.75 0.0469
0.77 0.0439
0.8 0.0389
0.82 0.0353
0.85 0.0294
0.87 0.0251
0.9 0.0181
0.92 0.0131
0.95 0.0049
0.97 -0.0009
0.98 -0.0039
0.99 -0.0071
1 -0.0104

0.002 -0.0093
0.005 -0.016
0.01 -0.0221
0.02 -0.0295
0.03 -0.0344
0.04 -0.0381
0.05 -0.0412
0.07 -0.0462
0.1 -0.0517
0.12 -0.0547
0.15 -0.0585
0.17 -0.0606
0.2 -0.0633
0.22 -0.0647
0.25 -0.0666
0.28 -0.068
0.3 -0.0687
0.32 -0.0692
0.35 -0.0696
0.37 -0.0696
0.4 -0.0692
0.42 -0.0688
0.45 -0.0676
0.48 -0.0657
0.5 -0.0644
0.53 -0.0614
0.55 -0.0588
0.58 -0.0543
0.6 -0.0509
0.63 -0.0451
0.65 -0.041
0.68 -0.0346
0.7 -0.0302
0.73 -0.0235
0.75 -0.0192
0.77 -0.015
0.8 -0.0093
0.83 -0.0048
0.85 -0.0024
0.87 -0.0013
0.89 -0.0008
0.92 -0.0016
0.94 -0.0035
0.95 -0.0049
0.96 -0.0066
0.97 -0.0085
0.98 -0.0109
0.99 -0.0137
1 -0.0163"""

    # Example dimensions from WingParameters
    root_chord = 1.819  # meters
    tip_chord = 0.4916  # meters
    semi_span = 5.0    # meters (half of wing span)    # Calculate and print volume with geometric parameters
    volume, details = calculate_fuel_volume(
        airfoil_data=airfoil_data,
        root_chord=root_chord,
        tip_chord=tip_chord,
        semi_span=semi_span,
        front_spar_x=0.15,  # front spar at 15% chord
        rear_spar_x=0.65,   # rear spar at 65% chord
        num_sections=20     # number of spanwise sections for integration
    )
    print(f"Total fuel volume: {volume:.2f} cubic meters")    # Create visualization with default wing parameters
    plot_wing_fuel_volume(
        airfoil_data=airfoil_data,
        root_chord=root_chord,
        tip_chord=tip_chord,
        semi_span=semi_span,
        front_spar_x=0.15,
        rear_spar_x=0.65,
        num_sections=20,
        show_parameters=True,
        colormap='YlOrRd'
    )