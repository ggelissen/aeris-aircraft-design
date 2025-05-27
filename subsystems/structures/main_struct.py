## Requirments:
# python=3.11
# numpy!=1.19.4

# Before running, make sure to run:
# pip install -r requirements.txt

from stl import mesh
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from mpl_toolkits import mplot3d
import matplotlib
import pyvista as pv
import numpy as np

from vspfunctions import print_all_params

matplotlib.use('Qt5Agg')
import openvsp as vsp
import vspfunctions

# Step 1: Loading analysis
import loading

# Step 2 Import geometric variables from Class I/II methods
# span =
# root_chord =
# tip_chord =
# sweep =

# Step 3: Create a VSP model using the imported geometric variables
vsp.ClearVSPModel()

# Add fuselage
fuse_id = vsp.AddGeom("FUSELAGE", "")

# Add wing
wing_id = vsp.AddGeom("WING", "")
wing_model = vsp.AddFeaStruct(wing_id)

# Set fuselage length
vsp.SetParmVal(fuse_id, "Length", "Design", 15.0)

# Find all wing parameters and print them. You can do this for other geometric objects as well.
print_all_params(wing_id)

# Set wing parameters like this:
# vsp.SetParmVal(geometric_object, "name_of_parameter", "group_name", new_value)
vsp.SetParmVal(wing_id, "Span", "XSec_1", 10.0)
vsp.SetParmVal(wing_id, "Root_Chord", "XSec_1", 3.0)
vsp.SetParmVal(wing_id, "Tip_Chord", "XSec_1", 1.5)
vsp.SetParmVal(wing_id, "Sweep", "XSec_1", 30.0)

# Set airfoil
vsp.InsertXSec(wing_id, 0, vsp.XS_FOUR_SERIES)  # Insert a four-series airfoil at the first cross-section
vsp.SetParmVal(wing_id, "Camber", "XSecCurve_0", 0.02)    # 2% camber
vsp.SetParmVal(wing_id, "CamberLoc", "XSecCurve_0", 0.4)  # at 40% chord
vsp.SetParmVal(wing_id, "ThickChord", "XSecCurve_0", 0.12)  # 12% thickness

# Position wing on fuselage
vsp.SetParmVal(wing_id, "X_Rel_Location", "XForm", 5.0)
vsp.SetParmVal(wing_id, "Z_Rel_Location", "XForm", 0)

# Add wingribs
num_wingribs = 10 # in total
ribs = []
for i in range(num_wingribs):
    ribs.append(vsp.AddFeaPart(wing_id, wing_model, vsp.FEA_RIB))

# add v_tail
hstab_id = vsp.AddGeom("WING")
vsp.SetGeomName(hstab_id, "Horizontal_Stabilizer")

# Position it at the tail (move along X and Z)
vsp.SetParmVal(hstab_id, "X_Rel_Location", "XForm", 10.0)  # Tail of the fuselage
vsp.SetParmVal(hstab_id, "Z_Rel_Location", "XForm", 0.5)   # Slight vertical offset

# Set orientation (v-tail, so dihedral = 40)
vsp.SetParmVal(hstab_id, "Dihedral", "XSec_1", 40.0)

# Symmetry around XZ plane (so it spans both sides)
vsp.SetParmVal(hstab_id, "Sym_Planar_Flag", "Sym", vsp.SYM_XZ)

# Size stabilizers
vsp.SetParmVal(hstab_id, "Span", "XSec_1", 5.0)
vsp.SetParmVal(hstab_id, "Tip_Chord", "XSec_1", 1.0)
vsp.SetParmVal(hstab_id, "Root_Chord", "XSec_0", 1.5)

# Add engines
pod_id = vsp.AddGeom("POD")
#print_all_params(pod_id)  # Print all parameters for the engine pod
vsp.SetGeomName(pod_id, "Fuselage_Engine")
vsp.SetParmVal(pod_id, "Length", "Design", 4.0)     # Length of the engine pod
vsp.SetParmVal(pod_id, "FineRatio", "Design", 6)     # Radius to Length ratio
vsp.SetParmVal(pod_id, "X_Rel_Location", "XForm", 8.50)   # Longitudinal position
vsp.SetParmVal(pod_id, "Y_Rel_Location", "XForm", 0.0)    # Side offset (0 = centerline)
vsp.SetParmVal(pod_id, "Z_Rel_Location", "XForm", 2)   # Vertical offset (on top of fuselage)




# Step 4: Simulate aircraft with loads

# Step 5: Change Structural variables to optimise for mass

# Step 6: Save progress and share optimised variables to other subsystems. Share aircraft 3D model to aerodynamics.

vsp.Update()

# Save as VSP3 file
vsp.WriteVSPFile("aircraft_model.vsp3")

# Export to STL or other formats
vsp.ExportFile("aircraft_model.stl", vsp.SET_ALL, vsp.EXPORT_STL)

# PLOTTING
# Load the STL file
# Load STL
your_mesh = mesh.Mesh.from_file('aircraft_model.stl')
points = your_mesh.vectors.reshape(-1, 3)

# Unique points and triangle faces
unique_points, idx = np.unique(points, axis=0, return_inverse=True)
faces = idx.reshape(-1, 3)

# Convert to pyvista format
faces_with_size = np.hstack([np.full((faces.shape[0], 1), 3), faces])  # '3' means triangle
pv_mesh = pv.PolyData(unique_points, faces_with_size)

# Plot with smooth shading
pv_mesh.plot(smooth_shading=True, color='lightgray', show_edges=False)